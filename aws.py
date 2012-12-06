"""
  Sync site to S3
  ================
  
  A Hyde publisher that scans all files in your site and
  uploads them to S3 with the same directory structure.
  
  In addition, the script will optionally:
  * gzip compress any HTML, SVG, CSS and Javascript files it 
    finds and add the appropriate 'Content-Encoding' header.
  * set a far future 'Expires' header for optimal caching.
  * only upload files if they have been modified since the 
    last upload.
  
  Copy this file to your hyde/ext/publishers/ directory
  to use it to upload your site
  
  Note: This script requires the Python boto library and a
  valid entry in the site.yaml file of your Hyde site
    
  
  Example site.yaml entry
  ------------------------
  
  publisher:           
      bff: (call it whatever you want)
          type: hyde.ext.publishers.aws.AWS
          url: s3://www.yourdomain.com
          AWS_ACCESS_KEY_ID: YOURACCESSKEY
          AWS_SECRET_ACCESS_KEY: YourSecretSpecialKeyGoesHere     
          expires: true (optional)
          check_mtime: true (optional)
          gzip: true (optional)       
          verbose: true (optional)
          
  Example usage (command line)         
  ----------------------------
  hyde publish -p bff
  
  
  This code was originally found at:
   https://texample.googlecode.com/svn-history/r159/trunk/apps/s3sync/management/commands/s3sync.py
  and has been modified to work with Hyde

"""
import datetime
import email
import mimetypes
import optparse
import os
import sys
import time

from hyde.fs import File, Folder
from hyde.publisher import Publisher

from hyde.util import getLoggerWithNullHandler
logger = getLoggerWithNullHandler('hyde.ext.publishers.aws')

# Make sure boto is available
try:
    import boto
    import boto.exception
except ImportError:
    raise ImportError, "The boto Python library is not installed."
    
try:
    from fs.osfs import OSFS
    from fs.path import pathjoin
    from fs.opener import fsopendir
except ImportError:
    logger.error("The AWS publisher requires PyFilesystem v0.4 or later.")
    logger.error("`pip install -U fs` to get it.")
    raise
    
class AWS(Publisher):
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_BUCKET_NAME = ''
    DIRECTORY = ''
    FILTER_LIST = ['.DS_Store',]
    GZIP_CONTENT_TYPES = (
        'text/html',
        'text/css',
        'application/javascript',
        'application/x-javascript',
        'application/x-font-ttf',
        'application/pdf',
        'image/svg+xml'
    )
    LONG_EXPIRY_CONTENT_TYPES = (
        'text/css',
        'application/javascript',
        'application/x-javascript',
        'application/x-font-ttf',
        'application/pdf',
        'image/jpeg',
        'image/png',        
        'image/svg+xml'
    )
    LONG_EXPIRY_DAYS = 100
    SHORT_EXPIRY_DAYS = 0.5
    
    upload_count = 0
    skip_count = 0

    def initialize(self, settings):    
      self.settings = settings
      self.url = settings.url
      self.check_mtime = getattr(settings,"check_mtime",False)
      self.check_etag = getattr(settings,"check_etag",False)
      self.do_gzip = getattr(settings,"gzip",False)
      self.do_expires = getattr(settings,"expires",False)
      self.do_force = getattr(settings,"force",False)
      self.verbosity = getattr(settings,"verbose",False)
      
      if self.verbosity == True:
        print (self.AWS_BUCKET_NAME)

      # Check for AWS keys in settings
      if not hasattr(self.settings, 'AWS_ACCESS_KEY_ID') or \
         not hasattr(self.settings, 'AWS_SECRET_ACCESS_KEY'):
         raise CommandError('Missing AWS keys from settings file.  Please' +
                   'supply both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.')
      else:
          self.AWS_ACCESS_KEY_ID = self.settings.AWS_ACCESS_KEY_ID
          self.AWS_SECRET_ACCESS_KEY = self.settings.AWS_SECRET_ACCESS_KEY

      self.AWS_BUCKET_NAME = str.lstrip(self.url,'s3://')   
      self.DIRECTORY = self.site.config.deploy_root_path.path

    def publish(self):
        if not self.site.config.deploy_root_path.exists:
            raise Exception("Please generate the site first")
        
        else:
          # Now call the syncing method to walk the directory and
          # upload all files found.        
          self.sync_s3()

          print
          print "%d files uploaded." % (self.upload_count)
          print "%d files skipped." % (self.skip_count)

    def sync_s3(self):
        """
        Walks the media directory and syncs files to S3
        """
        bucket, key = self.open_s3()
        os.path.walk(self.DIRECTORY, self.upload_s3,
            (bucket, key, self.AWS_BUCKET_NAME, self.DIRECTORY))

    def compress_string(self, s):
        """Gzip a given string."""
        import cStringIO, gzip
        zbuf = cStringIO.StringIO()
        zfile = gzip.GzipFile(mode='wb', compresslevel=9, fileobj=zbuf)
        zfile.write(s)
        zfile.close()
        return zbuf.getvalue()

    def open_s3(self):
        """
        Opens connection to S3 returning bucket and key
        """
        conn = boto.connect_s3(self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        try:
            bucket = conn.get_bucket(self.AWS_BUCKET_NAME)
        except boto.exception.S3ResponseError:
            bucket = conn.create_bucket(self.AWS_BUCKET_NAME)
        return bucket, boto.s3.key.Key(bucket)

    def upload_s3(self, arg, dirname, names):
        """
        This is the callback to os.path.walk and where much of the work happens
        """
        bucket, key, bucket_name, root_dir = arg # expand arg tuple

        if not root_dir.endswith('/'):
            root_dir = root_dir + '/'

        for file in names:
            headers = {}

            if file in self.FILTER_LIST:
                continue # Skip files we don't want to sync

            filename = os.path.join(dirname, file)
            if os.path.isdir(filename):
                continue # Don't try to upload directories

            file_key = filename[len(root_dir):]

            # Check if file on S3 is older than local file, if so, upload
            if not self.do_force:
                s3_key = bucket.get_key(file_key)
                if s3_key:
                    s3_datetime = datetime.datetime(*time.strptime(
                        s3_key.last_modified, '%a, %d %b %Y %H:%M:%S %Z')[0:6])
                    local_datetime = datetime.datetime.utcfromtimestamp(
                        os.stat(filename).st_mtime)
                    if local_datetime < s3_datetime:
                        self.skip_count += 1
                        if self.verbosity == True:
                            print "File %s hasn't been modified since last " \
                                "being uploaded" % (file_key)
                        continue

            # File is newer, let's process and upload
            if self.verbosity > 0:
                print "Uploading %s..." % (file_key)

            content_type = mimetypes.guess_type(filename)[0]
            if content_type:
                headers['Content-Type'] = content_type
            file_obj = open(filename, 'rb')
            file_size = os.fstat(file_obj.fileno()).st_size
            filedata = file_obj.read()
            if self.do_gzip:
                # Gzipping only if file is large enough (>1K is recommended) 
                # and only if file is a common text type (not a binary file)
                if file_size > 1024 and content_type in self.GZIP_CONTENT_TYPES:
                    filedata = self.compress_string(filedata)
                    headers['Content-Encoding'] = 'gzip'
                    if self.verbosity == True:
                        print "\tgzipped: %dk to %dk" % \
                            (file_size/1024, len(filedata)/1024)
            if self.do_expires:
                if content_type in self.LONG_EXPIRY_CONTENT_TYPES:
                    expiration_date = self.LONG_EXPIRY_DAYS
                else:
                    expiration_date = self.SHORT_EXPIRY_DAYS
                # HTTP/1.0
                headers['Expires'] = '%s GMT' % (email.Utils.formatdate(
                    time.mktime((datetime.datetime.now() +
                    datetime.timedelta(days=expiration_date)).timetuple())))
                # HTTP/1.1
                headers['Cache-Control'] = 'max-age %d' % (3600 * 24 * expiration_date)
                if self.verbosity == True:
                    print "\texpires: %s" % (headers['Expires'])
                    print "\tcache-control: %s" % (headers['Cache-Control'])

            try:
                key.name = file_key
                key.set_contents_from_string(filedata, headers, replace=True)
                key.make_public()
            except boto.s3.connection.S3CreateError, e:
                print "Failed: %s" % e
            except Exception, e:
                print e
                raise
            else:
                self.upload_count += 1

            file_obj.close()