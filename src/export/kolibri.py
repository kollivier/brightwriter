import logging
import os
import shutil
import tempfile
import uuid

from ricecooker import config
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

    temp_dir = None

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

        assert self.temp_dir, "Chef's temp_dir must be set before running."
        extract_path = os.path.join(self.temp_dir, 'imscp_package')
        os.makedirs(extract_path, exist_ok=True)
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
    with tempfile.TemporaryDirectory() as chef_path:
        os.chdir(chef_path)
        try:
            chef = BrightWriterExportChef()
            chef.temp_dir = chef_path
            chef.zip_path = imscp_zip
            args, options = chef.parse_args_and_options()
            args['thumbnails'] = True
            args['command'] = 'dryrun'
            logging.info("Creating channel...")
            channel = chef.run(args, options)
            channel = config.PROGRESS_MANAGER.channel
            logging.info("Starting export to db...")
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
    with tempfile.TemporaryDirectory() as chef_path:
        os.chdir(chef_path)
        try:
            chef = BrightWriterExportChef()
            chef.temp_dir = chef_path
            chef.zip_path = imscp_zip
            os.environ['STUDIO_TOKEN'] = token
            args, options = chef.parse_args_and_options()
            args['thumbnails'] = True
            args['command'] = 'uploadchannel'
            args['token'] = token
            chef.run(args, options)
            logging.info("Upload to Studio complete...")
        finally:
            os.chdir(old_dir)
            LOGGER.removeHandler(log_handler)
