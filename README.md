# Sync site to S3 #
<<<<<<< HEAD

A [Hyde](http://pydoc.net/hyde/latest/) publisher that scans all the files in your site and uploads them to S3 with the same directory structure.
  
In addition, the script will optionally:

- gzip compress any HTML, SVG, CSS and Javascript files it finds and add the appropriate 'Content-Encoding' header
- set an 'Expires' header for each file for optimal caching
- only upload modified files

Just copy this file to your {$PYTHONPATH}/hyde/ext/publishers/ directory to use it 

Note: This script requires the Python boto library and a valid entry in the site.yaml file of your Hyde site
  
## Example site.yaml entry ##
=======
  
  A [Hyde](http://pydoc.net/hyde/latest/) publisher that scans all files in your site and
  uploads them to S3 with the same directory structure.
  
  In addition, the script will optionally:
  
  - gzip compress any HTML, SVG, CSS and Javascript files it 
    finds and add the appropriate 'Content-Encoding' header.
  - set a far future 'Expires' header for optimal caching.
  - only upload files if they have been modified since the 
    last upload.
  
  Copy this file to your hyde/ext/publishers/ directory
  to use it to upload your site
  
  Note: This script requires the Python boto library and a
  valid entry in the site.yaml file of your Hyde site
    
  
## Example site.yaml entry ##

  
>>>>>>> 91207988ae4e8130a0815183505fdf7c41d55b37
      publisher:           
		  bff: (call it whatever you want)
			  type: hyde.ext.publishers.aws.AWS
			  url: s3://www.yourdomain.com
			  AWS_ACCESS_KEY_ID: YOURACCESSKEY
			  AWS_SECRET_ACCESS_KEY: YourSecretSpecialKeyGoesHere     
<<<<<<< HEAD
              gzip: true (optional) 
              expires: true (optional)
			  check_mtime: true (optional)      
			  verbose: true (optional)
			  
## Example Usage (Command Line) ##
	  hyde publish -p bff
    
## License ##
=======
			  expires: true (optional)
			  check_mtime: true (optional)
			  gzip: true (optional)       
			  verbose: true (optional)
			  
## Example Usage (Command Line) ##

	  hyde publish -p bff
    
## License ##

>>>>>>> 91207988ae4e8130a0815183505fdf7c41d55b37
This code was originally found [here](https://texample.googlecode.com/svn-history/r159/trunk/apps/s3sync/management/commands/s3sync.py), and was distributed under an MIT license.
