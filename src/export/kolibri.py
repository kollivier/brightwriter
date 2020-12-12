import logging
import os
import shutil
import tempfile

from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses
from ricecooker.classes.files import get_hash

from imscp.core import extract_from_zip
from imscp.ricecooker_utils import make_topic_tree_with_entrypoints


class BrightWriterExportChef(SushiChef):
    """
    The chef class that takes care of uploading channel to the content curation server.

    We'll call its `main()` method from the command line script.
    """
    channel_info = {
        'CHANNEL_SOURCE_DOMAIN': "brightwriter.net",
        'CHANNEL_SOURCE_ID': "brightwriter-test",
        'CHANNEL_TITLE': "Sample IMSCP upload from brightwriter",
        'CHANNEL_DESCRIPTION': "",
        'CHANNEL_LANGUAGE': "en",
    }

    def construct_channel(self, **kwargs):
        """
        Create ChannelNode and build topic tree.
        """
        # create channel
        channel = self.get_channel()

        license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")

        with tempfile.TemporaryDirectory() as extract_path:
            imscp_dict = extract_from_zip(self.zip_path, license,
                    extract_path)
            hashed_zip_filename = os.path.join(tempfile.tempdir, get_hash(self.zip_path) + '.zip')
            shutil.copy2(self.zip_path, hashed_zip_filename)
            for topic_dict in imscp_dict['organizations']:
                if 'title' not in topic_dict and 'children' in topic_dict:
                    topic_dict['title'] = topic_dict['children'][0]['title']

                topic_tree = make_topic_tree_with_entrypoints(license, hashed_zip_filename, topic_dict, extract_path)
                print('Adding topic tree to channel:', topic_tree)
                channel.add_child(topic_tree)

        return channel


def export_project_to_kolibri_studio(imscp_zip):
    """
    This code will run when the sushi chef is called from the command line.
    """
    chef = BrightWriterExportChef()
    chef.zip_path = imscp_zip
    args, options = chef.parse_args_and_options()
    args['command'] = 'uploadchannel'
    args['token'] = os.environ.get('STUDIO_TOKEN')
    chef.run(args, options)
    logging.info("Run complete...")
