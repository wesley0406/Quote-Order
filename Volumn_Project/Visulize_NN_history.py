import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def visualize_training_history(excel_file = None):
    """
    Load training history from Excel and create Plotly visualizations for loss, MAE, and MSE.
    
    Args:
        excel_file: Path to Excel file containing training history
    """
    try:
        # Load Excel file
        df = pd.read_excel(excel_file)
        if df.empty:
            print("Error: Training history Excel file is empty")
            return
        
        # Verify required columns
        required_cols = ['epoch', 'loss', 'mae', 'mse', 'val_loss', 'val_mae', 'val_mse']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Missing required columns in {excel_file}")
            return
        
        # Create subplots
        # fig = make_subplots(
        #     rows = 2, cols=1,
        #     subplot_titles=('Training and Validation Loss', 'Training and Validation MSE'),
        #     shared_xaxes=True,
        #     vertical_spacing=0.1
        # )
        fig = go.Figure()
        
        # Plot Loss
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['loss'], mode='lines', name='Training Loss', line=dict(color='blue'))
        )
        
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['val_mse'], mode='lines', name='Validation MSE', line=dict(color='red'), yaxis="y2")
        )
        
        # Update layout
        fig.update_layout(
            title='Training Loss and Validation MSE',
            xaxis=dict(
                title='Epoch',
                tickmode='linear',
                tick0=0,
                dtick=5
            ),
            yaxis=dict(
                title='Training Loss',
                tickfont=dict(color='blue')
            ),
            yaxis2=dict(
                title='Validation MSE',
                tickfont=dict(color='red'),
                overlaying='y',
                side='right'
            ),
            height=500,
            showlegend=True
        )
        # Save and display
        history_folder = r"C:\Users\wesley\Desktop\workboard\Volumn_Project\History"
        fig.write_html('training_history_plot.html')
        print("Plot saved to training_history_plot.html")
        fig.show()
        
    except Exception as e:
        print(f"Error in visualize_training_history: {str(e)}")
        raise

if __name__ == "__main__":
    target = input("Enter the history file : ")
    visualize_training_history(target)