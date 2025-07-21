from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, TextMessage
from linebot.v3.messaging.models import PushMessageRequest
import plotly.express as px
import plotly.io as pio
import tempfile
import os

# Replace with your credentials
channel_access_token = 'KKP6lxqEpBaBTbz7EmkxDW/H+1D1L++WHImL7uO9ArPBrTEPn634dI0Z5hVYp45fwJfBWpWHqqNTMLalsB2naKENDleaI8RbvcOPHn4wXmSR96ldio4KA277+5He3BOrbn2coRtjoP/2Cw4BLZuF1AdB04t89/1O/w1cDnyilFU='
user_id = 'U3045600efc0fbbde741b7f855422a3f4'  # Recipient’s LINE user ID (or your own for testing)

# Initialize LINE Bot API
configuration = Configuration(access_token=channel_access_token)


# Assuming you have ApiClient and configuration set up
with ApiClient(configuration) as api_client:
    messaging_api = MessagingApi(api_client)
    try:
        # Create a sample Plotly chart
        fig = px.scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17], title="Sample Scatter Plot")
        
        # Save the chart as a PNG file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        pio.write_image(fig, temp_file.name, format='png')
        
        # Upload the image to LINE's Content API
        with open(temp_file.name, 'rb') as image_file:
            response = messaging_api.upload_message_content(
                file=image_file,
                content_type='image/png'
            )
        
        # Extract the content URL from the response
        # Note: The exact response structure depends on the SDK. Adjust if needed.
        content_url = response.content_url  # Hypothetical attribute; verify with your SDK
        
        # Send the chart as an image message
        push_message_request = PushMessageRequest(
            to=user_id,
            messages=[
                TextMessage(text='Here is your Plotly chart!'),
                ImageMessage(
                    original_content_url=content_url,
                    preview_image_url=content_url,
                    content_provider=ContentProvider(type='line')
                )
            ]
        )
        messaging_api.push_message(push_message_request)
        print("Chart message sent successfully!")
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
    except Exception as e:
        print(f"Error sending message: {e}")

