import logging
import os
import shutil
import tempfile
import uuid

from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses
from ricecooker.classes.files import get_hash
from ricecooker.config import LOGGER

from imscp.core import extract_from_zip
from imscp.ricecooker_utils import make_topic_tree_with_entrypoints

import settings


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
        if not settings.ProjectSettings["UUID"]:
            settings.ProjectSettings["UUID"] = str(uuid.uuid4())
            settings.ProjectSettings.SaveAsXML()
        self.channel_info['CHANNEL_SOURCE_ID'] = settings.ProjectSettings["UUID"]

        channel = self.get_channel()

        license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")

        with tempfile.TemporaryDirectory() as extract_path:
            imscp_dict = extract_from_zip(self.zip_path, license,
                    extract_path)
            hashed_zip_filename = os.path.join(tempfile.tempdir, get_hash(self.zip_path) + '.zip')
            shutil.copy2(self.zip_path, hashed_zip_filename)
            topics = []
            for topic_dict in imscp_dict['organizations']:
                if 'title' not in topic_dict and 'children' in topic_dict:
                    topic_dict['title'] = topic_dict['children'][0]['title']

                topic_tree = make_topic_tree_with_entrypoints(license, hashed_zip_filename, topic_dict, extract_path)
                print('Adding topic tree to channel:', topic_tree)
                topics.append(topic_tree)

            # if there's one topic, treat that topic as the root node
            # Note: Always the case right now,
            if len(topics) == 1:
                channel.title = topics[0].title
                channel.description = topics[0].description
                for subtopic in topics[0].children:
                    channel.add_child(subtopic)
            else:
                for topic in topics:
                    channel.add_child(topic)

        return channel

def export_project_to_kolibri_db(imscp_zip, local_directory, log_handler):
    """
    This code will run when the sushi chef is called from the command line.
    """
    LOGGER.addHandler(log_handler)
    old_dir = os.getcwd()
    os.chdir(settings.ProjectDir)
    try:
        chef = BrightWriterExportChef()
        chef.zip_path = imscp_zip
        args, options = chef.parse_args_and_options()
        args_and_options = args.copy()
        args_and_options.update(options)
        channel = chef.construct_channel(**args_and_options)
        channel.export_to_kolibri_db(local_directory)
        logging.info("Run complete...")
    finally:
        os.chdir(old_dir)
        LOGGER.removeHandler(log_handler)



def export_project_to_kolibri_studio(imscp_zip, token, log_handler):
    """
    This code will run when the sushi chef is called from the command line.
    """
    LOGGER.addHandler(log_handler)
    old_dir = os.getcwd()
    os.chdir(settings.ProjectDir)
    try:
        chef = BrightWriterExportChef()
        chef.zip_path = imscp_zip
        args, options = chef.parse_args_and_options()
        args['command'] = 'uploadchannel'
        args['token'] = token
        chef.run(args, options)
        logging.info("Run complete...")
    finally:
        os.chdir(old_dir)
        LOGGER.removeHandler(log_handler)
