import warnings
warnings.filterwarnings("ignore")

## Derive the BASE_DIR based on the current file location
import os
import sys
temp = os.path.dirname(os.path.abspath(__file__))
vals = temp.split('/')
BASE_DIR = '/'.join(vals[:-2])
BASE_DIR = '%s/' % BASE_DIR
sys.path.insert(0, BASE_DIR)

import json
import time
from openai import OpenAI
from bson import ObjectId
from utom_agents.functions import conversations as convo
from utom_user.functions import user_creation, user_management
from utom_workspace.functions import workspace_creation, workspace_management
from utom_project.functions import project_creation, project_management
from utom_feature.functions import feature_management
from utom_task.functions import task_creation
from utom_pages.functions import pages_creation, pages_management
# from utom_feature.functions import feature_creation_llm_prompts as llm_prompts

"""
*** something for later is that you need to remove the conversation history from the raw feature metadata and make it something that is read in
"""


"""    
Feature Pre-Prompts
"""
# feature_creation_pre_prompt = """You are a specialist in product management and have worked as a VP of product in many organisations, tasked with assisting a coworkers in defining and refining a feature they want to build. Your goal is to lead a thoughtful and structured conversation to fully understand the feature and its context.

# Begin the discussion with an engaging question, such as, "Tell me about what you want to build." Follow up with unique and non-repetitive questions to clarify the feature's purpose and scope. Ensure that each question is distinct and asked one at a time to maintain a smooth conversation flow. Only proceed to the next question after receiving a response to the current one. Focus on these aspects:

# Understanding the Idea and Its Purpose
# - Feature Clarification: What is the feature, and what specific problem is it addressing? What pain points are users currently experiencing that this feature will alleviate?
# - Primary Users and Context: Who are the target users? What are the primary use cases and scenarios in which the feature will be utilized?

# Business Alignment and Impact
# - Business Value: What is the strategic business goal of the feature? How does it align with the overall product vision and competitive positioning?
# - Success Metrics: What are the measurable indicators of success for this feature? (e.g., engagement rates, retention, revenue growth, user satisfaction)

# Challenges and Opportunities
# - Risks and Constraints: What are the known technical, operational, or market-related risks or constraints? Are there external dependencies or regulatory considerations?

# Implementation-Oriented Questions
# - Data Requirements: What specific data (user inputs, external integrations, etc.) is required for the feature to function effectively? Where will this data come from, and how will it be validated?
# - Core Functionalities: What are the essential functionalities that this feature must include to meet its objectives? What are the "nice-to-haves" that could be added if time and resources allow?
# - AI and Automation Opportunities: What tasks or processes within this feature could benefit from automation or AI? For example, is there scope for machine learning, predictive modeling, or intelligent recommendations?
# - Integration Points: How will the feature integrate with existing systems, tools, or workflows? Are there APIs, SDKs, or infrastructure components that need to be leveraged or developed?
# - User Experience and Scalability: How will the feature maintain a seamless user experience as it scales? What design considerations will ensure simplicity and intuitive interactions?

# Respond conversationally and adapt your approach based on the user's answers. Aim to deliver both insights and actionable guidance.
# """



"""   
LLM Related Functions
"""
def initialize_feature_creation_convo():
    from utom_agents.functions import conversations as convo

    feature_creation_pre_prompt = """You are a specialist in product management and have worked as a VP of product in many organisations. Your task is to lead a natural and engaging conversation about a new feature with a member of the team.

    PHASE 1 - INITIAL FEATURE EXPLORATION
    Start the conversation warmly, perhaps with, "Great! Let's get started. Tell me what you want to build." Engage in a dynamic dialogue, asking questions one at a time, and allowing the user to respond with 'skip' if they wish to move on. Your questions should naturally flow from the conversation, covering these key areas:
    - Feature purpose and problem solving
    - Target users and use cases
    - Business value and alignment
    - Technical considerations
    - Data requirements
    - Integration points
    - Success metrics
    - Risks and constraints

    PHASE 2 - USER FLOW DEEP DIVE
    Once the initial exploration is complete, summarize the key insights and smoothly transition into a deeper dive with follow-up questions about:
    - Specific user interaction patterns
    - Screen-to-screen transitions
    - Edge cases and error scenarios
    - User preferences and customization
    - Performance expectations

    Throughout the conversation, ensure to:
    1. Ask one question at a time
    2. Adapt questions based on the context and previous answers
    3. Move to the next question immediately if the user responds with 'skip'
    4. Provide a clear transition between phases
    5. Summarize findings before moving to Phase 2
    """

    conversation_id, conversation_starter = convo.initialize_conversation(feature_creation_pre_prompt)

    return conversation_id, conversation_starter

def initialize_feature_creation_convo_from_existing_feature(project_id, feature_id):
    """
    Initializes a new conversation for feature creation based on an existing feature
    
    Args:
        project_id (str): ID of the project containing the feature
        feature_id (str): ID of the feature to expand
        
    Returns:
        tuple: (conversation_id, conversation_starter)
    """
    # Get project metadata
    project_metadata = project_management.get_project_by_id(project_id) or {"project_title": "", "project_description": "", "target_audience": [], "business_goals": [], "acceptance_criteria": [], "technical_requirements": []}
    
    # Get feature metadata
    feature_metadata = feature_management.get_feature_by_id(feature_id) or {"feature_details": {"feature_name": "", "feature_description": ""}}
    
    # Extract feature details
    feature_details = feature_metadata.get("feature_details", {})
    feature_name = feature_details.get("feature_name", "")
    feature_description = feature_details.get("feature_description", "")
    
    # Create a custom pre-prompt for continuing from an existing feature
    feature_pre_prompt = f"""You are a specialist in product management and have worked as a VP of product in many organisations. Your task is to lead a natural and engaging conversation about expanding a feature that has already been identified as part of a project.

PROJECT CONTEXT:
- Project Title: {project_metadata.get("project_title", "")}
- Project Description: {project_metadata.get("project_description", "")}
- Target Audience: {", ".join([str(audience) for audience in project_metadata.get("target_audience", [])])}
- Business Goals: {", ".join([str(goal) for goal in project_metadata.get("business_goals", [])])}
- Acceptance Criteria: {", ".join([str(criterion) for criterion in project_metadata.get("acceptance_criteria", [])])}
- Technical Requirements: {", ".join([str(req) for req in project_metadata.get("technical_requirements", [])])}

FEATURE DETAILS:
- Feature Name: {feature_name}
- Feature Description: {feature_description}

You are continuing a conversation about this feature that has already been identified as important for the project. Your goal is to help flesh it out with more details.

PHASE 1 - DETAILED FEATURE EXPLORATION
Start the conversation warmly, acknowledging the existing feature information. Your first message should be brief, friendly, and directly related to the specific feature and project context. Ensure the response is no more than 30 words and should focus on continuing the conversation to create the feature. Engage in a dynamic dialogue, asking questions one at a time, and allowing the user to respond with 'skip' if they wish to move on. Your questions should naturally flow from the conversation, covering these key areas:
- Detailed feature purpose and problem solving beyond the initial description
- Specific target users and use cases within the project's audience
- Technical considerations and implementation details
- Data requirements and storage needs
- Integration points with other systems or features
- Success metrics specific to this feature
- Risks and constraints for implementation

PHASE 2 - USER FLOW DEEP DIVE
Once the initial exploration is complete, summarize the key insights and smoothly transition into a deeper dive with follow-up questions about:
- Specific user interaction patterns
- Screen-to-screen transitions
- Edge cases and error scenarios
- User preferences and customization
- Performance expectations

Throughout the conversation, ensure to:
1. Ask one question at a time
2. Adapt questions based on the context and previous answers
3. Move to the next question immediately if the user responds with 'skip'
4. Provide a clear transition between phases
5. Summarize findings before moving to Phase 2
6. Acknowledge the existing information and build upon it rather than repeating questions about information you already have
"""

    # Initialize the conversation with the custom pre-prompt
    conversation_id, conversation_starter = convo.initialize_conversation(feature_pre_prompt)
    
    return conversation_id, conversation_starter

def extract_json_from_llm_response(text):
    # Regex to find JSON-like structure in the text
    # Using a simpler regex pattern that matches balanced braces
    depth = 0
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                json_str = text[start:i+1]
                try:
                    # Convert the JSON string to a Python dictionary
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)
                    return None
    
    print("No JSON structure found in the text.")
    return None

def generate_initial_feature_metadata_from_feature_creation_conversation(conversation_id, model_name="o3-mini"):
    # Initialize OpenAI client for this function call
    utom_openai_api_key = os.getenv('utom_openai_api_key')
    client = OpenAI(api_key=utom_openai_api_key)
    
    # Convert conversation history to a more readable format for the prompt
    conversation_history = convo.get_cleaned_conversation_history_as_list(conversation_id)  
    formatted_conversation = "\n".join([
        f"{message['role'].upper()}: {message['content']}"
        for message in conversation_history
    ])
    
    prompt = f"""Given the following conversation about a feature:
    {formatted_conversation}

    Generate a comprehensive feature analysis. Return the response in the following JSON format:
    {{
        "feature_name": "<3-5 word name that captures the core functionality>",
        "feature_description": "<50-80 word in-depth description of the feature's purpose and value>",
        "user_flows": [
            {{
                "flow_id": "flow_1",
                "title": "<clear, action-oriented title of this flow step>",
                "description": "<20-50 word detailed description explaining what happens in this step, why it's important, and how it connects to the overall user journey>"
            }},
            {{
                "flow_id": "flow_2",
                "title": "<clear, action-oriented title>",
                "description": "<detailed explanation of the step>"
            }},
            // ... at least 20 detailed flow steps
        ],
        "execution_steps": [
            {{
                "step_number": 1,
                "title": "<specific, detailed title of implementation step>",
                "roles": ["<role1>", "<role2>"],
                "description": "<detailed description of implementation requirements>",
                "dependencies": [],
                "estimated_hours": <number>,
                "complexity": "<low/medium/high>"
            }},
            // ... at least 20 detailed execution steps
        ]
    }}

    Ensure:
    1. Feature name and description are concise and clear
    2. User flows:
       - Have unique, sequential flow_ids
       - Include clear, action-oriented titles
       - Provide comprehensive descriptions that explain the what, why, and how
       - Cover the entire user journey from start to finish
       - Include edge cases and alternative paths
       - Are written from the user's perspective
    3. Execution steps are highly specific and include:
       - Clear dependencies between steps
       - Realistic time estimates
       - All relevant roles
       - Detailed descriptions of implementation requirements
    4. Steps are ordered in logical implementation sequence
    5. Return only valid JSON with no additional text"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a product analyst that returns only valid JSON objects with no additional text."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        max_completion_tokens=10000,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content.strip()
    
    try:
        feature_details = json.loads(content)
    except json.JSONDecodeError:
        try:
            feature_details = extract_json_from_llm_response(content)
        except Exception as e:
            print(e)
            feature_details = {
                "feature_name": "",
                "feature_description": "",
                "user_flow": []
            }

    # Add metadata to the feature details
    feature_details['user_flow_reviewed'] = False
    feature_details['conversation_history'] = conversation_history

    return feature_details

def generate_detailed_design_brief(feature_details, model_name="o3-mini"):
    """
    Generates a detailed design brief from feature metadata to guide UI designers in creating the feature flow.
    
    Args:
        feature_details (dict): The feature details to process
        model_name (str): Name of the OpenAI model to use
    
    Returns:
        dict: Feature details with added design brief
    """
    # Initialize OpenAI client for this function call
    utom_openai_api_key = os.getenv('utom_openai_api_key')
    client = OpenAI(api_key=utom_openai_api_key)

    # Create a generic prompt with clear instructions for each section
    prompt = f"""Given the following feature metadata:
    {json.dumps(feature_details, indent=2)}

    Generate a comprehensive design brief for UI designers based on the specific feature requirements above. Include a detailed component catalog for each screen and an exhaustive list of all required endpoints. Return the response in the following JSON format without any comments or explanatory text:
    {{
        "design_brief": {{
            "overview": "A concise summary of the design purpose and scope based on the feature requirements",
            "objectives": "3-5 key objectives the design must achieve to fulfill the feature requirements",
            "constraints": "Technical, business, or user constraints that impact the design",
            "design_system": {{
                "color_palette": {{
                    "primary": {{
                        "main": "Appropriate hex color code for the main primary color",
                        "light": "Appropriate hex color code for the light primary variant",
                        "dark": "Appropriate hex color code for the dark primary variant",
                        "contrast_text": "Appropriate hex color code for text on primary background"
                    }},
                    "secondary": {{
                        "main": "Appropriate hex color code for the main secondary color",
                        "light": "Appropriate hex color code for the light secondary variant",
                        "dark": "Appropriate hex color code for the dark secondary variant",
                        "contrast_text": "Appropriate hex color code for text on secondary background"
                    }},
                    "background": {{
                        "default": "Appropriate hex color code for default background",
                        "paper": "Appropriate hex color code for paper/card background"
                    }}
                }},
                "component_themes": {{
                    "buttons": {{
                        "primary": {{
                            "bg": "Appropriate hex color code for primary button background",
                            "hover": "Appropriate hex color code for primary button hover state",
                            "active": "Appropriate hex color code for primary button active state"
                        }},
                        "secondary": {{
                            "bg": "Appropriate hex color code for secondary button background",
                            "hover": "Appropriate hex color code for secondary button hover state",
                            "active": "Appropriate hex color code for secondary button active state"
                        }}
                    }}
                }},
                "spacing_scale": {{
                    "compact": "Appropriate rem value for compact spacing",
                    "normal": "Appropriate rem value for normal spacing",
                    "relaxed": "Appropriate rem value for relaxed spacing"
                }}
            }}
        }},
        "screens": {{
            "screen_identifier_1": {{
                "screen_id": "A unique identifier for this screen",
                "screen_name": "A descriptive name for this screen based on its purpose",
                "screen_description": "A brief description of this screen's purpose and functionality",
                "execution_dependencies": [1, 2, 3],
                "implementation_phase": "The appropriate implementation phase for this screen",
                
                "component_catalog": {{
                    "navigation_components": {{
                        "component_example_1": {{
                            "type": "The component type (e.g., button, input, card)",
                            "description": "Detailed description of this component's purpose and functionality",
                            "required_elements": [
                                "List of required sub-elements for this component"
                            ],
                            "variants": [
                                "List of variations needed for this component"
                            ],
                            "props": {{
                                "prop1": "Data type and description",
                                "prop2": "Data type and description"
                            }},
                            "states": [
                                "List of possible states for this component"
                            ],
                            "interactions": [
                                "List of ways users can interact with this component"
                            ]
                        }}
                    }},
                    "form_components": {{
                        "component_example_2": {{
                            "type": "The component type",
                            "description": "Detailed description",
                            "required_elements": ["Required elements"],
                            "variants": ["Variants"],
                            "props": {{
                                "prop1": "Data type and description"
                            }},
                            "states": ["States"],
                            "interactions": ["Interactions"]
                        }}
                    }}
                }},

                "component_hierarchy": {{
                    "layout": {{
                        "type": "The layout type appropriate for this screen",
                        "children": [
                            {{
                                "type": "A component type from the catalog",
                                "execution_step_dependency": 1,
                                "children": ["Child components if applicable"]
                            }}
                        ]
                    }}
                }},

                "required_endpoints": [
                    {{
                        "name": "A descriptive name for this endpoint based on its function",
                        "path": "The API path for this endpoint",
                        "method": "The HTTP method (GET, POST, PUT, DELETE, etc.)",
                        "description": "Detailed description of what this endpoint does and why it's needed",
                        "request": {{
                            "query_params": {{
                                "param_name": {{
                                    "type": "The data type of this parameter",
                                    "description": "Description of this parameter's purpose",
                                    "required": true,
                                    "default": "Default value if applicable"
                                }}
                            }},
                            "headers": {{
                                "Authorization": "Description of required authorization"
                            }},
                            "body": {{
                                "field_name": "Data type and description"
                            }}
                        }},
                        "response": {{
                            "success": {{
                                "status": 200,
                                "data": {{
                                    "field_name": "Data type and description"
                                }}
                            }},
                            "error_cases": [
                                {{
                                    "scenario": "Description of error scenario",
                                    "status": 400,
                                    "response": {{
                                        "error": "Error code",
                                        "message": "Error message"
                                    }}
                                }}
                            ]
                        }},
                        "usage_context": "Explanation of where and how this endpoint's data is used in the UI"
                    }}
                ],

                "screen_states": {{
                    "view_modes": [
                        {{
                            "mode": "Name of this view mode",
                            "layout": "Layout type for this mode",
                            "active_components": ["Components active in this mode"]
                        }}
                    ],
                    "conditional_elements": [
                        {{
                            "element": "Element identifier",
                            "display_condition": "Condition for displaying this element",
                            "execution_step_dependency": 1
                        }}
                    ]
                }},

                "data_management": {{
                    "state_structure": {{
                        "local_state": {{
                            "state_key": "Data type and description"
                        }},
                        "global_state": {{
                            "required_slices": ["State slices needed"],
                            "mutations_needed": ["Mutations needed"]
                        }}
                    }},
                    "caching_strategy": {{
                        "cache_keys": ["Cache keys needed"],
                        "invalidation_triggers": ["Events that should invalidate cache"],
                        "execution_step_dependency": 1
                    }}
                }},

                "screen_data": {{
                    "dummy_data": {{
                        "static_content": {{
                            "images": [
                                {{
                                    "purpose": "Purpose of this image",
                                    "url": "Placeholder URL or description",
                                    "aspect_ratio": "Appropriate aspect ratio",
                                    "alt_text": "Descriptive alt text"
                                }}
                            ],
                            "text_content": {{
                                "headlines": ["Example headlines appropriate for this screen"],
                                "descriptions": ["Example descriptions appropriate for this screen"]
                            }}
                        }},
                        "dynamic_content": {{
                            "list_items": [
                                {{
                                    "template": {{
                                        "title": "Example title format",
                                        "description": "Example description format",
                                        "image_url": "Placeholder URL or description",
                                        "metadata": {{
                                            "created_at": "Timestamp format",
                                            "status": ["Possible status values"]
                                        }}
                                    }},
                                    "count": 5
                                }}
                            ]
                        }}
                    }}
                }}
            }}
        }}
    }}

    Instructions for generating the design brief:
    1. Create a design brief that directly addresses the specific feature requirements in the provided metadata
    2. Generate at least 2-3 screens with unique IDs based on the user flows in the feature details
    3. For each screen:
       - Create a comprehensive component catalog with components organized by logical categories
       - Include all necessary components for the screen's functionality
       - Define detailed component properties, states, and interactions
       - Specify all required API endpoints with complete request/response specifications
       - Define appropriate screen states and view modes
       - Create realistic data management strategies
       - Include appropriate dummy data examples
    4. Ensure all screens have appropriate execution dependencies linked to the execution steps in the feature details
    5. Generate a color palette and design system that aligns with the feature's purpose and target audience
    6. Return only valid JSON with no comments or explanatory text
    7. Replace all placeholder text with specific, contextually appropriate content
    8. Ensure the design brief is comprehensive, detailed, and directly applicable to the feature requirements
    """

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior UI/UX engineer that specializes in creating detailed design briefs. Analyze the feature requirements carefully and generate a comprehensive design brief with specific, contextually appropriate content. Return only valid JSON objects with no comments or explanatory text."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_completion_tokens=15000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            design_brief = json.loads(content)
            
            # If we get here, JSON parsing succeeded
            feature_details['design_brief'] = design_brief
            return feature_details

        except json.JSONDecodeError as e:
            retry_count += 1
            print(f"Attempt {retry_count}: Error parsing JSON response: {str(e)}")
            
            if retry_count >= max_retries:
                print(f"Failed to generate valid JSON after {max_retries} attempts")
                # Return the original feature_details without a design brief
                return feature_details
                
            # Wait briefly before retrying
            time.sleep(1)
            
        except Exception as e:
            print(f"Error generating design brief: {str(e)}")
            return feature_details


def save_feature_to_db(feature_metadata):
    """
    Saves feature metadata to MongoDB
    
    Args:
        feature_metadata (dict): Feature metadata dictionary to save
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        db.project_features.insert_one(feature_metadata)
    finally:
        client.close()

def get_feature_details(feature_id):
    """
    Retrieves feature details from MongoDB using the feature_id
    
    Args:
        feature_id (str): The ID of the feature to retrieve
    
    Returns:
        dict: Feature details dictionary
    """
    from utom_databases.functions import mongo_utils as mongo
    client = mongo.initialise_mongo_cloud_db_client()
    try:
        db = client['utom_features']
        feature_details = db.project_features.find_one({"feature_id": feature_id})
        if feature_details is None:
            raise ValueError(f"Feature with ID {feature_id} not found")
        return feature_details
    finally:
        client.close()

def create_new_feature_from_user_conversation(feature_creation_input_metadata):
    """ 
    Prelim
    """
    workspace_id = feature_creation_input_metadata["workspace_id"]
    project_id = feature_creation_input_metadata["project_id"]
    creator_id = feature_creation_input_metadata["creator_id"]
    conversation_id = feature_creation_input_metadata["conversation_id"]

    # Check if workspace exists, use placeholder if not
    workspace_metadata = workspace_management.get_workspace_details(workspace_id)
    if workspace_metadata is None:
        workspace_metadata = {
            'workspace_id': 'placeholder_workspace_id',
            'name': 'Placeholder Workspace'
        }

    # Check if project exists, use placeholder if not
    project_metadata = project_management.get_project_by_id(project_id)
    if project_metadata is None:
        project_metadata = {
            'project_id': 'placeholder_project_id',
            'name': 'Placeholder Project'
        }

    user_metadata = user_management.get_user_by_id(creator_id)

    """ 
    Create the initial feature metadata dict
    """
    feature_id = str(ObjectId())
    created_at = int(time.time())
    project_feature_metadata_dict = {
        "feature_id": feature_id,
        "created_at": created_at,
        "workspace_id": workspace_metadata['workspace_id'],
        "project_id": project_metadata['project_id'], 
        "creator_id": user_metadata['user_id'],
        "workspace_metadata": workspace_metadata,
        "project_metadata": project_metadata,
        "creator_metadata": user_metadata,
        "members": [user_metadata['user_id']],  # Initialize with creator
        "status": "planning",
        "percentage_complete": 0
    }

    """ 
    1 - Analyse the conversation and generate feature details
    """
    feature_details = generate_initial_feature_metadata_from_feature_creation_conversation(conversation_id)
    project_feature_metadata_dict['feature_details'] = feature_details

    """   
    2 - Save the project feature
    """
    save_feature_to_db(project_feature_metadata_dict)
    feature_id = project_feature_metadata_dict['feature_id']

    return feature_id

def verify_user_flows_and_generate_design_briefs(feature_id):
    """
    Verifies user flows and generates detailed design briefs for the given feature.
    
    Args:
        feature_id (str): The ID of the feature to process.
    
    Returns:
        None
    """
    # Retrieve feature details from the database using the feature_id
    feature_metadata = get_feature_details(feature_id)
    
    # Extract feature details from the metadata
    feature_details = feature_metadata['feature_details']
    
    # Mark user flow as reviewed
    feature_details['user_flow_reviewed'] = True
    
    # Generate a detailed design brief from the feature details
    feature_details = generate_detailed_design_brief(feature_details)
    
    # Update the feature metadata with the new feature details
    feature_metadata['feature_details'] = feature_details
    
    # Update the feature in the database with the new metadata
    feature_management.update_feature(feature_metadata)

"""   
New Functions For Feature E2E Creation
"""
import os
import json
from openai import OpenAI

def extract_json_from_llm_response(text):
    # Regex to find JSON-like structure in the text
    # Using a simpler regex pattern that matches balanced braces
    depth = 0
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                json_str = text[start:i+1]
                try:
                    # Convert the JSON string to a Python dictionary
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)
                    return None
    
    print("No JSON structure found in the text.")
    return None

def generate_user_flows_and_execution_steps_from_feature_creation_conversation(conversation_id, is_placeholder_feature=True):
    # Initialize OpenAI client for this function call
    utom_openai_api_key = os.getenv('utom_openai_api_key')
    client = OpenAI(api_key=utom_openai_api_key)

    # Convert conversation history to a more readable format for the prompt
    if is_placeholder_feature:
        conversation_history = convo.get_cleaned_conversation_history_as_list(conversation_id, True)  
    else:
        conversation_history = convo.get_cleaned_conversation_history_as_list(conversation_id, False)  

    formatted_conversation = "\n".join([
        f"{message['role'].upper()}: {message['content']}"
        for message in conversation_history
    ])

    prompt = f"""Given the following conversation about a feature:
    {formatted_conversation}

    Generate a comprehensive feature analysis that can be implemented by a junior startup team. Return the response in the following JSON format:
    {{
        "user_flows": [
            {{
                "flow_id": "flow_1",
                "title": "<clear, action-oriented title of this flow step>",
                "description": "<20-50 word detailed description explaining what happens in this step, why it's important, and how it connects to the overall user journey>"
            }},
            {{
                "flow_id": "flow_2",
                "title": "<clear, action-oriented title>",
                "description": "<detailed explanation of the step>"
            }}
            // ... dynamically generate flow steps based on the complexity of the user journey, aim for at least 10
            // Ensure each flow step is clearly defined with a unique flow_id, a descriptive title, and a comprehensive description
            // The description should explain the purpose of the step, its importance, and how it fits into the overall user journey
            // Include edge cases and alternative paths to cover the entire user experience
        ],
        "execution_steps": [
            {{
                "step_number": 1,
                "title": "<specific, detailed title of implementation step>",
                "roles": ["<role1>", "<role2>"],
                "description": "<detailed description of implementation requirements>",
                "dependencies": [],
                "estimated_hours": <number>,
                "complexity": "<low/medium/high>",
                "action_plan": [
                    {{
                        "action_id": 1,
                        "action_title": "<specific technical action to take>",
                        "technical_details": "<specific technical implementation details including code patterns, libraries, or frameworks to use>",
                        "expected_outcome": "<clear description of what successful completion looks like>"
                    }},
                    // ... include 3-5 specific technical actions per execution step
                ]
            }}
            // ... at least 20 detailed execution steps
            // Each execution step should be clearly defined with a step_number, a descriptive title, and a detailed description
            // The description should include implementation requirements, dependencies, estimated hours, and complexity level
            // Ensure steps are ordered logically and cover all necessary roles and dependencies
        ]
    }}

    Ensure:
    1. Feature name and description are concise and clear
    2. User flows:
        - Have unique, sequential flow_ids
        - Include clear, action-oriented titles
        - Provide comprehensive descriptions that explain the what, why, and how
        - Cover the entire user journey from start to finish
        - Include edge cases and alternative paths
        - Are written from the user's perspective
    3. Execution steps are highly specific and include:
        - Clear dependencies between steps
        - Realistic time estimates
        - Roles limited to: product manager, product designer, frontend engineer, backend engineer, llm engineer, and devops engineer
        - Detailed descriptions of implementation requirements
        - A comprehensive action plan with specific technical implementation details
    4. Steps are ordered in logical implementation sequence
    5. Return only valid JSON with no additional text"""

    model_name="o3-mini"
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a product analyst that returns only valid JSON objects with no additional text."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        max_completion_tokens=10000,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content.strip()

    try:
        userflow_and_execution_steps_metadata = json.loads(content)
    except json.JSONDecodeError:
        try:
            userflow_and_execution_steps_metadata = extract_json_from_llm_response(content)
        except Exception as e:
            print(e)
            userflow_and_execution_steps_metadata = {
                "user_flows": [],
                "execution_steps": []
            }
    
    return userflow_and_execution_steps_metadata

def generate_pages_for_feature_from_design_brief(pages_creation_input_metadata, feature_details):

    feature_pages = []
    pages_metadata = []
    design_brief = feature_details['design_brief']
    screen_briefs = pages_creation.generate_screen_design_briefs(design_brief)

    for screen_design_brief in screen_briefs:
        page_metadata = pages_creation.generate_utom_page_from_screen_design_brief(screen_design_brief, pages_creation_input_metadata)
        feature_pages.append({
            "page_id": page_metadata["page_id"],
            "screen_name": page_metadata["screen_design_brief"]["screen_id"]
        })
        pages_metadata.append(page_metadata)
    feature_details['feature_pages'] = feature_pages
    
    return feature_details, pages_metadata

def generate_feature_details_e2e_one_shot(feature_creation_input_metadata, project_metadata):
    """
    Generate feature details end-to-end in one shot.

    This function orchestrates the process of generating user flows, execution steps, 
    detailed design briefs, pages, and tasks for a feature, and updates the feature 
    metadata in the database.

    Args:
        feature_creation_input_metadata (dict): Metadata required for feature creation.
        project_metadata (dict): Metadata of the project.

    Returns:
        dict: Updated feature metadata.
    """

    # Extract necessary IDs from feature creation input metadata
    workspace_id = feature_creation_input_metadata["workspace_id"]
    project_id = feature_creation_input_metadata["project_id"]
    feature_id = feature_creation_input_metadata["feature_id"]
    creator_id = feature_creation_input_metadata["creator_id"]
    conversation_id = feature_creation_input_metadata["conversation_id"]

    # Create metadata for pages creation
    pages_creation_input_metadata = {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "creator_id": creator_id,
        "feature_id": feature_id,
    }

    # Generate user flows and execution steps from the conversation
    print('Generating user flows and execution steps')
    userflow_and_execution_steps_metadata = generate_user_flows_and_execution_steps_from_feature_creation_conversation(conversation_id)
    print('Generated user flows and execution steps')

    # Retrieve feature metadata by feature ID
    feature_metadata = feature_management.get_feature_by_id(feature_id)
    del feature_metadata['_id']

    # Update feature metadata with user flows and execution steps
    print('Generating detailed design brief')
    feature_metadata['feature_details']['user_flows'] = userflow_and_execution_steps_metadata['user_flows']
    feature_metadata['feature_details']['execution_steps'] = userflow_and_execution_steps_metadata['execution_steps']
    feature_details = feature_metadata['feature_details']
    # Generate a detailed design brief for the feature
    ## - this ensures that the feature details are only the ones that are needed for the design brief
    feature_details = {key: feature_details[key] for key in ['feature_name', 'feature_description', 'priority', 'dependencies', 'integration_points', 'user_flow_reviewed', 'user_flows', 'execution_steps']}

    feature_details = generate_detailed_design_brief(feature_details)
    print('Generated detailed design brief')
    # Save the feature to the database - interim save for independent page functionality
    feature_management.update_feature(feature_metadata)

    # Generate pages for the feature from the design brief
    print('Generating pages for the feature from the design brief')
    feature_details, pages_metadata = generate_pages_for_feature_from_design_brief(pages_creation_input_metadata, feature_details)
    feature_metadata['feature_details'] = feature_details
    print('Generated pages for the feature from the design brief')
    # Generate tasks for the feature
    print('Generating tasks for the feature')
    feature_tasks = task_creation.generate_and_assign_tasks(project_metadata, feature_metadata, pages_metadata)
    print('Generated tasks for the feature')
    # Update feature metadata with generated tasks and mark as fleshed out
    feature_metadata['feature_details']['feature_tasks'] = feature_tasks
    feature_metadata['feature_fleshed_out'] = True
    feature_management.update_feature(feature_metadata)

    return feature_metadata

def process_generate_feature_details_e2e_one_shot_task(task_json_string):
    """
    Process a task to generate feature details end-to-end in one shot.
    
    This function:
    1. Parses the task JSON
    2. Extracts the necessary parameters
    3. Calls the generate_feature_details_e2e_one_shot function
    4. Returns the result
    
    Args:
        task_json_string (str): JSON string containing the task details
        
    Returns:
        dict: The generated feature metadata
    """
    import json
    
    # Parse the task JSON
    task_dict = json.loads(task_json_string)
    
    # Extract the task message data
    print('Started the feature creation task')
    task_message_dict = task_dict['task_message_dict']
    
    # Extract the input parameters
    feature_creation_input_metadata = task_message_dict['feature_creation_input_metadata']
    project_metadata = task_message_dict['project_metadata']
    
    # Log some information about the task
    workspace_id = feature_creation_input_metadata.get('workspace_id', 'N/A')
    project_id = feature_creation_input_metadata.get('project_id', 'N/A')
    feature_id = feature_creation_input_metadata.get('feature_id', 'N/A')
    
    print(f'Processing feature creation for workspace: {workspace_id}, project: {project_id}, feature: {feature_id}')
    
    # Call the feature creation function
    feature_metadata = generate_feature_details_e2e_one_shot(
        feature_creation_input_metadata,
        project_metadata
    )
    
    print('Generated feature details successfully')
    
    return feature_metadata

"""
Future Enhancements:

1. Collaboration Features
   - Version approval workflows
   - Change request tracking
   - Task assignments
   - Team member comments/feedback on specific versions
   - Assigned reviewers/developers
   - Status tracking (draft, review, approved, etc.)

2. Endpoint Analysis
   - Visual analysis of page structure
   - Automatic endpoint detection
   - Endpoint dependency tracking
   - API integration requirements
   - Data flow mapping

3. Chat Features
   - Team discussion storage
   - Comment threading
   - Notification system
   - Real-time collaboration
   - Change tracking and notifications

4. Advanced Version Control
   - Branch management for different design directions
   - Merge capabilities for combining features
   - Rollback functionality
   - Diff viewing between versions
   - Version comparison tools

5. Accessibility Requirements
   - ARIA landmarks and roles
   - Keyboard navigation patterns
   - Screen reader optimizations
   - Color contrast requirements
   - Focus management
   - Dynamic content announcements

6. Performance Requirements
   - Loading thresholds
   - Code splitting strategies
   - Data prefetching
   - Asset loading optimization
   - Performance monitoring points
   - Caching strategies
"""