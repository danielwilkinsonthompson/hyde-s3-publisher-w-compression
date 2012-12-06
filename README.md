# Sync Hyde Site to S3 #

A [Hyde](http://pydoc.net/hyde/latest/) publisher that scans all the files in your site and uploads them to S3 with the same directory structure.
  
In addition, the script will optionally:

- gzip any HTML, SVG, CSS and Javascript files it finds and add the appropriate 'Content-Encoding' header
- set an 'Expires' header for each file for optimal caching
- only upload modified files

Just copy this file to your hyde/ext/publishers/ directory to use it 

Note: This script requires the 'boto' library and a valid entry in your site.yaml file
  
## Example site.yaml entry ##
      publisher:           
		  bff: #(call it whatever you want)
			  type: hyde.ext.publishers.aws.AWS
			  url: s3://www.yourdomain.com
			  AWS_ACCESS_KEY_ID: YOURACCESSKEY
			  AWS_SECRET_ACCESS_KEY: YourSecretSpecialKeyGoesHere     
              gzip: true (optional) 
              expires: true (optional)
			  check_mtime: true (optional)      
			  verbose: true (optional)
			  
## Example Usage (Command Line) ##
	  hyde publish -p bff
    
## License ##
This is a modification of the Django S3 loader I found [here](https://texample.googlecode.com/svn-history/r159/trunk/apps/s3sync/management/commands/s3sync.py), which was distributed under an MIT license.