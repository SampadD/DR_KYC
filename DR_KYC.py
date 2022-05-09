#import streamlit as st
import pandas as pd
import numpy as np
#import sys
#import json
import requests
#import datarobot as dr
#import networkx as nx
#from matplotlib.pyplot import figure
import streamlit as st
#from datarobot_predict import make_datarobot_deployment_predictions,main
#import matplotlib.pyplot as plt
#import datarobot_predict as dp ## REST API Code for classification
#import seaborn as sns
#from pyvis.network import Network
#import streamlit.components.v1 as components
#import Anomaly_Detection as AD ## REST API code for anomaly detection
import snowflake.connector
import base64
from PIL import Image
import pytesseract
from io import BytesIO
#import SessionState
#import streamlit.report_thread as ReportThread

#pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

st.set_page_config(layout = 'wide')

st.set_option('deprecation.showPyplotGlobalUse', False)

API_URL = 'https://cfds-ccm-prod.orm.datarobot.com/predApi/v1.0/deployments/{deployment_id}/predictions'    # noqa
API_KEY = st.secrets.datarobot.apikey
DATAROBOT_KEY = st.secrets.datarobot.drkey

DEPLOYMENT_ID = '60dac31a47efced2a2d503fb'



def process_image(image_name, lang_code):
	return pytesseract.image_to_string(image_name, lang=lang_code)

def print_data(data):
	print(data)

def output_file(filename, data):
	file = open(filename, "w+")
	file.write(data)
	file.close()

class DataRobotPredictionError(Exception):
    """Raised if there are issues getting predictions from DataRobot"""
    
def _raise_dataroboterror_for_status(response):
    """Raise DataRobotPredictionError if the request fails along with the response returned"""
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        err_msg = '{code} Error: {msg}'.format(
            code=response.status_code, msg=response.text)
        raise DataRobotPredictionError(err_msg)


def make_datarobot_deployment_predictions(data, deployment_id):
    """
    Make predictions on data provided using DataRobot deployment_id provided.
    See docs for details:
         https://app.datarobot.com/docs/predictions/api/dr-predapi.html

    Parameters
    ----------
    data : str
        If using CSV as input:
        Feature1,Feature2
        numeric_value,string

        Or if using JSON as input:
        [{"Feature1":numeric_value,"Feature2":"string"}]

    deployment_id : str
        The ID of the deployment to make predictions with.

    Returns
    -------
    Response schema:
        https://app.datarobot.com/docs/predictions/api/dr-predapi.html#response-schema

    Raises
    ------
    DataRobotPredictionError if there are issues getting predictions from DataRobot
    """
    # Set HTTP headers. The charset should match the contents of the file.
    headers = {
        # As default, we expect CSV as input data.
        # Should you wish to supply JSON instead,
        # comment out the line below and use the line after that instead:
        #'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Type': 'application/json; charset=UTF-8',

        'Authorization': 'Bearer {}'.format(API_KEY),
        'DataRobot-Key': DATAROBOT_KEY,
    }

    url = API_URL.format(deployment_id=deployment_id)

    # Prediction Explanations:
    # See the documentation for more information:
    # https://app.datarobot.com/docs/predictions/api/dr-predapi.html#request-pred-explanations
    # Should you wish to include Prediction Explanations or Prediction Warnings in the result,
    # Change the parameters below accordingly, and remove the comment from the params field below:

    params = {
        # If explanations are required, uncomment the line below
        # 'maxExplanations': 3,
        # 'thresholdHigh': 0.5,
        # 'thresholdLow': 0.15,
        # Uncomment this for Prediction Warnings, if enabled for your deployment.
        # 'predictionWarningEnabled': 'true',
    }
    # Make API request for predictions
    predictions_response = requests.post(
        url,
        data=data,
        headers=headers,
        # Prediction Explanations:
        # Uncomment this to include explanations in your prediction
        # params=params,
    )
    _raise_dataroboterror_for_status(predictions_response)
    # Return a Python dict following the schema in the documentation
    return predictions_response.json()



def image_predictions(image_str,deployment_id):
    df = pd.DataFrame([image_str], columns = ['image'])
    df_json = df.to_json(orient = 'records')
    return make_datarobot_deployment_predictions(df_json, deployment_id)
    
    
    
# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"])

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

rows = run_query("Select * from DATAROBOT_DEMO.SAMPAD.IMAGES_DOCS_EKYC where APPROVAL is NULL;")

#a = 0
#st.sidebar

#row1, row2, row3 = st.rows([1,1,5])

with st.sidebar:
    st.image("DR_logo.png")
    st.markdown('# DR KYC\n## KYC validation App\n[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://github.com/SampadD/DR_KYC)\n\nDR KYC App is a web app powered by DataRobot models. It allows for \n- Direct DB connection\n- AI powered document classification\n- OCR for data extraction\n\n\n\n     ')
    #st.markdown('This app pulls data from a Snowflake DB containing KYC documents. It uses a DatRobot model to decipher type of the document. Futhermore it attempt to extract data from the document')
    

if 'key' not in st.session_state:
    st.session_state.key = 0

    
col1, col2, col3 = st.columns([1,1,5])

with col1:
    if st.button("Previous"):
        st.session_state.key = st.session_state.key-1
        #st.text(ss.x)

with col2:
    if st.button("Next"):
        st.session_state.key = st.session_state.key+1

st.text("Customer ID: " + str(rows[st.session_state.key][1]))
    
image_64_decode = base64.b64decode(rows[st.session_state.key][0]) 

st.image(image_64_decode)

prediction = image_predictions(rows[st.session_state.key][0],DEPLOYMENT_ID)

st.markdown("#### Prediction: " + str(prediction['data'][0]['prediction']).upper())
#st.text(prediction['data'][0]['prediction'])

st.markdown("#### Confidence of PAN")
st.text(str(prediction['data'][0]['predictionValues'][3]['value']*100))


#col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns([1,1,1,1,1])

# with col_p1:
#     st.text(str(prediction['data'][0]['predictionValues'][0]['label'] )+ " " +  str(prediction['data'][0]['predictionValues'][0]['value']*100))

# with col_p2:
#     st.text(str(prediction['data'][0]['predictionValues'][1]['label'] )+ " " +  str(prediction['data'][0]['predictionValues'][1]['value']*100))

# with col_p3:
#     st.text(str(prediction['data'][0]['predictionValues'][2]['label'] )+ " " +  str(prediction['data'][0]['predictionValues'][2]['value']*100))

# with col_p4:
#     st.text(str(prediction['data'][0]['predictionValues'][3]['label'] )+ " " +  str(prediction['data'][0]['predictionValues'][3]['value']*100))

# with col_p5:
#     st.text(str(prediction['data'][0]['predictionValues'][4]['label'] )+ " " +  str(prediction['data'][0]['predictionValues'][4]['value']*100))


# if image_predictions(rows[st.session_state.key][0],DEPLOYMENT_ID)['data'][0]['prediction'] != 'pan':
#     st.text("It doesnt look like the document is a PAN card. It appears to be " + image_predictions(rows[st.session_state.key][0],DEPLOYMENT_ID)['data'][0]['prediction'])
# else:
#     st.text("PAN card detected")


data_eng = process_image(Image.open(BytesIO(image_64_decode)), "eng")

st.markdown("#### Document data - Extracted using OCR")

if data_eng == "":
    st.text("No data could be extracted. Ask for clear image")
else :
    st.text(data_eng)


ap_col1, ap_col2, ap_col3 = st.columns([1,1,5])

with ap_col1:
    if st.button("Approve"):
            run_query("Update DATAROBOT_DEMO.SAMPAD.IMAGES_DOCS_EKYC set APPROVAL = 'Yes' where ID = " + str(rows[st.session_state.key][1]))
            #st.session_state.key = st.session_state.key+1
    
with ap_col2:
    if st.button("Reject"):
            run_query("Update DATAROBOT_DEMO.SAMPAD.IMAGES_DOCS_EKYC set APPROVAL = 'No' where ID = " + str(rows[st.session_state.key][1]))
            #st.session_state.key = st.session_state.key+1
 
    



#st.image('DR.png')








