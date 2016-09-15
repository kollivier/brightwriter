from pew.rest_client import *

from local_settings import *

DOMAIN = "api-dev.brightsparc.io"


class BrightSparcClient(RESTClient):
    def __init__(self):
        global DOMAIN
        if "--local" in sys.argv:
            DOMAIN = "localhost:8000"

        super(BrightSparcClient, self).__init__(DOMAIN)

        self.client_id = brightwriter_client_id
        self.client_secret = brightwriter_client_secret

        self.set_domain(DOMAIN)

        self.sign_in(brightwriter_username, brightwriter_password)

    def post_error_report(self, data):
        self.call_api('/api/v2/bug_reports/', method="POST", data=json.dumps(data))
