import json
import logging
from utom_feature.processors.s3_processor import handle_s3_notification

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for S3 notifications
    
    Args:
        event (dict): Lambda event containing S3 notification
        context (object): Lambda context
        
    Returns:
        dict: Response containing status code and body
    """
    try:
        # Log incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process notification
        result = handle_s3_notification(event)
        
        # Log result
        if result['success']:
            logger.info(f"Successfully processed notification: {json.dumps(result)}")
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        else:
            logger.error(f"Failed to process notification: {json.dumps(result)}")
            return {
                'statusCode': 500,
                'body': json.dumps(result)
            }
            
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }