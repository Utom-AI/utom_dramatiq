import warnings
warnings.filterwarnings("ignore")

## Derive the BASE_DIR based on the current file location
import os
import sys
temp = os.getcwd()
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR
print(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import time
from bson.objectid import ObjectId

def get_feature_by_id(feature_id):
    """
    Retrieves feature metadata for a given feature ID
    
    Args:
        feature_id (str): ID of the feature
        
    Returns:
        dict: Feature metadata dictionary or None if not found
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        feature = db.project_features.find_one({"feature_id": feature_id})
        if feature:
            feature['_id'] = str(feature['_id'])
        return feature
    finally:
        client.close()

def get_project_features(project_id):
    """
    Retrieves all features for a given project
    
    Args:
        project_id (str): ID of the project
        
    Returns:
        list: List of feature metadata dictionaries
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        features = list(db.project_features.find({"project_id": project_id}))
        for feature in features:
            feature['_id'] = str(feature['_id'])
        return features
    finally:
        client.close()

def get_user_features(user_id):
    """
    Retrieves all features where the user is a feature member
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        list: List of feature metadata dictionaries
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        features = list(db.project_features.find({"members": {"$in": [user_id]}}))
        for feature in features:
            feature['_id'] = str(feature['_id'])
        return features
    finally:
        client.close()

def add_feature_member(feature_id, user_id):
    """
    Adds a team member to the feature
    
    Args:
        feature_id (str): ID of the feature
        user_id (str): ID of the user to add
        
    Returns:
        bool: True if successful, False if user already in team
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        result = db.project_features.update_one(
            {"feature_id": feature_id},
            {"$addToSet": {"feature_member_ids": user_id}}
        )
        return result.modified_count > 0
    finally:
        client.close()

def remove_feature_member(feature_id, user_id):
    """
    Removes a team member from the feature
    
    Args:
        feature_id (str): ID of the feature
        user_id (str): ID of the user to remove
        
    Returns:
        bool: True if successful, False if user not in team
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        result = db.project_features.update_one(
            {"feature_id": feature_id},
            {"$pull": {"feature_member_ids": user_id}}
        )
        return result.modified_count > 0
    finally:
        client.close()

def delete_feature(feature_id):
    """
    Deletes a feature from the database
    
    Args:
        feature_id (str): ID of the feature to delete
        
    Returns:
        bool: True if successful, False if feature not found
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        result = db.project_features.delete_one({"feature_id": feature_id})
        return result.deleted_count > 0
    finally:
        client.close()

def update_feature(feature_metadata):
    """
    Updates feature metadata with provided values
    
    Args:
        feature_metadata (dict): Dictionary containing the fields to update, including feature_id
            Example: {
                "feature_id": "123",
                "name": "New Feature Name",
                "description": "Updated description",
                "status": "in_progress",
                "percentage_complete": 50,
                ...
            }
        
    Returns:
        bool: True if successful, False if feature not found
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        feature_id = feature_metadata.get('feature_id')
        if not feature_id:
            return False
            
        result = db.project_features.update_one(
            {"feature_id": feature_id},
            {"$set": feature_metadata}
        )
        return result.modified_count > 0
    finally:
        client.close()

def get_feature_design_brief(feature_id):
    """
    Retrieves the design brief for a given feature
    
    Args:
        feature_id (str): ID of the feature
        
    Returns:
        dict: Design brief dictionary or None if not found
    """
    feature_metadata = get_feature_by_id(feature_id)
    if not feature_metadata or 'feature_details' not in feature_metadata:
        return None
        
    feature_details = feature_metadata['feature_details']
    return feature_details.get('design_brief')

def update_feature_design_brief(feature_id, design_brief):
    """
    Updates the design brief for a given feature
    
    Args:
        feature_id (str): ID of the feature
        design_brief (dict): New design brief data
        
    Returns:
        bool: True if successful, False if feature not found
    """
    feature_metadata = get_feature_by_id(feature_id)
    if not feature_metadata:
        return False
        
    feature_metadata['feature_details']['design_brief'] = design_brief
    return update_feature(feature_metadata)

def is_feature_fleshed_out(feature_id):
    """
    Checks if a feature has been fully fleshed out
    
    Args:
        feature_id (str): ID of the feature to check
        
    Returns:
        bool: True if the feature is fleshed out, False otherwise
    """
    feature_metadata = get_feature_by_id(feature_id)
    if not feature_metadata:
        return False
    
    # First check if the flag exists in the metadata
    if 'feature_fleshed_out' not in feature_metadata:
        return False
    
    # Then check if the flag is True
    return feature_metadata['feature_fleshed_out'] is True

