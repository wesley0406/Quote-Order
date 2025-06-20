import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def visualize_training_history(excel_file='training_history.xlsx'):
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
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Training and Validation Loss', 'Training and Validation MAE', 'Training and Validation MSE'),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # Plot Loss
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['loss'], mode='lines', name='Training Loss', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['val_loss'], mode='lines', name='Validation Loss', line=dict(color='red')),
            row=1, col=1
        )
        
        # Plot MAE
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['mae'], mode='lines', name='Training MAE', line=dict(color='blue')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['val_mae'], mode='lines', name='Validation MAE', line=dict(color='red')),
            row=2, col=1
        )
        
        # Plot MSE
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['mse'], mode='lines', name='Training MSE', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['epoch'], y=df['val_mse'], mode='lines', name='Validation MSE', line=dict(color='red')),
            row=3, col=1
        )
        
        # Update layout
        fig.update_layout(
            title='Neural Network Training History',
            height=900,
            showlegend=True,
            xaxis3=dict(title='Epoch'),
            yaxis1=dict(title='Loss (Huber)'),
            yaxis2=dict(title='MAE (mm³)'),
            yaxis3=dict(title='MSE (mm³²)')
        )
        
        # Save and display
        fig.write_html('training_history_plot.html')
        print("Plot saved to training_history_plot.html")
        fig.show()
        
    except Exception as e:
        print(f"Error in visualize_training_history: {str(e)}")
        raise

if __name__ == "__main__":
    visualize_training_history()