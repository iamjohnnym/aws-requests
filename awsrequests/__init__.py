import requests
import os
from .signing import get_headers_for_request
from .connections import AWSConnections

try:
    HAS_BOTO=True
    import botocore.credentials
    import botocore.session
    import botocore.exceptions
    import boto3
except:
    HAS_BOTO=False

# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())

class AwsRequester(AWSConnections):
    def __init__(self, **kwargs):
        """
        **kwargs gets set to self.args as a dict

        REQUIRED
        :param: aws_asset = 'ec2', 'sts', 's3', 'dynamodb', any of the services
                            that amazon offers through boto3
        :param: region = region to connect to
        :param: aws_account = aws account # to access
        :param: role = role used for your arn
        :param: role_name = the name in which will be seen through the
                            aws cloudtrails

        OPTIONAL
        :param: assume

        arn gets automagically generated when self.loadClient() is called:

        arn:aws:iam::${aws_account}:role/${role}
        """
        self.args = kwargs
        # example args
        #self.args['aws_asset'] = 'ec2'
        #self.args['region'] = 'us-east-1'
        #self.args['aws_account'] = '123456789098'
        #self.args['role'] = 'RoleAssume'
        #self.args['role_name'] = 'Example'
        # if you want to use boto3 sts, set this value to true
        #self.args['assume'] = True
        self.loadClient()

    def loadClient(self):
        self.client = self.login()

    def request(self, method, url,
                params=None,
                data=None,
                headers=None,
                cookies=None,
                files=None,
                auth=None,
                timeout=None,
                allow_redirects=True,
                proxies=None,
                hooks=None,
                stream=None,
                verify=None,
                cert=None,
                json=None,
                time=None):
        """Constructs and sends a :class:`Request <Request>`.
        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
        :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': ('filename', fileobj)}``) for multipart encoding upload.
        :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How long to wait for the server to send data
            before giving up, as a float, or a :ref:`(connect timeout, read
            timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect following is allowed.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param verify: (optional) if ``True``, the SSL cert will be verified. A CA_BUNDLE path can also be provided.
        :param stream: (optional) if ``False``, the response content will be immediately downloaded.
        :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        :param time: (optional) time to put on the request
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        session = requests.sessions.Session()
        # TODO: build auth headers here

        # TODO: build query params if they were passed in sepeartely

        req = requests.Request(method, url,
                               data=data,
                               headers=headers,
                               params=params,
                               cookies=cookies,
                               files=files,
                               auth=auth,
                               json=json,
                               hooks=hooks
                               )
        prepped = req.prepare()
        aws_auth_headers = get_headers_for_request(
                url,
                self.args['region'],
                'execute-api',
                self.temp_creds["Credentials"]["AccessKeyId"],
                self.temp_creds["Credentials"]
                               ['SecretAccessKey'],
                self.temp_creds["Credentials"]["SessionToken"],
                payload=prepped.body,
                method=prepped.method,
                t=time
                )
        prepped.headers.update(aws_auth_headers)

        response = session.send(prepped,
                                stream=stream,
                                verify=verify,
                                proxies=proxies,
                                cert=cert,
                                timeout=timeout,
                                allow_redirects=allow_redirects
                                )

        session.close()
        return response

    def get(self, url, params=None, **kwargs):
        """Sends a GET request.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, params=params, **kwargs)

    def options(self, url, **kwargs):
        """Sends a OPTIONS request.
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('options', url, **kwargs)

    def head(self, url, **kwargs):
        """Sends a HEAD request.
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        kwargs.setdefault('allow_redirects', False)
        return self.request('head', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """Sends a POST request.
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        return self.request('post', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        """Sends a PUT request.
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        return self.request('put', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """Sends a PATCH request.
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        return self.request('patch', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """Sends a DELETE request.
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        return self.request('delete', url, **kwargs)
