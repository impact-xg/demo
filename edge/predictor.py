import json
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import os
from datetime import datetime

# Import the custom attention layer from the training script
class SelfAttention(tf.keras.layers.Layer):
    """
    Custom Self-Attention Layer
    This layer applies attention over the time steps of a sequence, allowing the model
    to focus on the most relevant parts of the time series for prediction.
    """
    def __init__(self, attention_units=128, **kwargs):
        self.attention_units = attention_units
        super(SelfAttention, self).__init__(**kwargs)
        
    def build(self, input_shape):
        # input_shape = (batch_size, time_steps, features)
        self.time_steps = input_shape[1]
        self.features = input_shape[2]
        
        # Dense layer to compute attention scores
        self.W_attention = self.add_weight(name='W_attention',
                                          shape=(self.features, self.attention_units),
                                          initializer='glorot_uniform',
                                          trainable=True)
        
        self.b_attention = self.add_weight(name='b_attention',
                                         shape=(self.attention_units,),
                                         initializer='zeros',
                                         trainable=True)
        
        # Context vector to compute attention weights
        self.u_attention = self.add_weight(name='u_attention',
                                          shape=(self.attention_units, 1),
                                          initializer='glorot_uniform',
                                          trainable=True)
        
        super(SelfAttention, self).build(input_shape)
    
    def call(self, inputs):
        # inputs shape: (batch_size, time_steps, features)
        
        # Step 1: Compute attention scores
        # (batch_size, time_steps, features) @ (features, attention_units) = (batch_size, time_steps, attention_units)
        score = tf.tanh(tf.tensordot(inputs, self.W_attention, axes=[[2], [0]]) + self.b_attention)
        
        # Step 2: Compute attention weights
        # (batch_size, time_steps, attention_units) @ (attention_units, 1) = (batch_size, time_steps, 1)
        attention_weights = tf.nn.softmax(tf.tensordot(score, self.u_attention, axes=[[2], [0]]), axis=1)
        
        # Step 3: Apply attention weights to input sequence
        # (batch_size, time_steps, 1) * (batch_size, time_steps, features) = (batch_size, time_steps, features)
        context_vector = attention_weights * inputs
        
        # Step 4: Sum over time dimension to get weighted representation
        # (batch_size, features)
        context_vector = tf.reduce_sum(context_vector, axis=1)
        
        return context_vector
    
    def compute_output_shape(self, input_shape):
        return (input_shape[0], input_shape[2])
    
    def get_config(self):
        config = super(SelfAttention, self).get_config()
        config.update({
            'attention_units': self.attention_units,
        })
        return config


class Predictor:
    def __init__(self, model_path="model_gru_with_attention.h5", scaler_path="scaler.save", seq_length=5):
        """
        Initialize the Predictor with the trained model and scaler.
        
        Args:
            model_path: Path to the saved model (.h5 file)
            scaler_path: Path to the saved scaler (.save file)
            seq_length: Sequence length used during training (default: 5)
        """
        print("Predictor initializing...")
        
        self.seq_length = seq_length
        self.model = None
        self.scaler = None
        self.feature_cols = None
        
        # Load the model with custom objects
        try:
            # Load the model with the custom SelfAttention layer
            self.model = tf.keras.models.load_model(
                model_path,
                custom_objects={'SelfAttention': SelfAttention}
            )
            print(f"Model loaded successfully from {model_path}")
            
            # Load the scaler
            self.scaler = joblib.load(scaler_path)
            print(f"Scaler loaded successfully from {scaler_path}")
            
            # Determine feature columns based on the new format (5 timestamps × 5 features = 25 features)
            self.feature_cols = [f"f{i}" for i in range(25)]
            
            print("Predictor initialized successfully.")
            
        except Exception as e:
            print(f"Error loading model or scaler: {e}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for model at: {model_path}")
            print(f"Looking for scaler at: {scaler_path}")
            raise

    def _extract_features_from_trace(self, trace_dict):
        """
        Extract features from a single trace dictionary.
        
        Args:
            trace_dict: Dictionary containing timestamp data
            
        Returns:
            Dictionary with flattened features
        """
        # Get all timestamp keys (excluding the main "timestamp" key)
        inner_keys = [k for k in trace_dict.keys() if k not in ["timestamp"]]
        inner_keys = sorted(inner_keys)
        
        # We expect 5 timestamps for a sequence length of 5
        if len(inner_keys) != self.seq_length:
            raise ValueError(f"Expected {self.seq_length} timestamps, but got {len(inner_keys)}")
        
        # Flatten the features in the same order as during training
        flat_features = []
        for key in inner_keys:
            entry = trace_dict[key]
            # Order: throughput, packets_lost, packet_loss_rate, jitter, speed
            flat_features.extend([
                entry["throughput"],
                entry["packets_lost"],
                entry["packet_loss_rate"],
                entry["jitter"],
                float(entry["speed"])  # Ensure speed is float
            ])
        
        # Create feature dictionary
        feature_dict = {}
        for i, val in enumerate(flat_features):
            feature_dict[f"f{i}"] = val
        
        return feature_dict

    def infer(self, trace_data):
        """
        Perform inference on the provided trace data.
        
        Args:
            trace_data: List of dictionaries containing network trace data
            
        Returns:
            List of predicted QoE values
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model or scaler not loaded properly")
        
        print(f"Processing {len(trace_data)} trace records...")
        
        predictions = []
        
        # Process each trace independently
        for i, trace in enumerate(trace_data):
            try:
                # Extract features from the trace
                features = self._extract_features_from_trace(trace)
                
                # Create a DataFrame with the features
                df = pd.DataFrame([features])
                
                # Normalize the features using the loaded scaler
                # We only normalize the feature columns, not QoE
                df_normalized = df.copy()
                df_normalized[self.feature_cols] = self.scaler.transform(df[self.feature_cols])
                
                # Reshape for model input: (1, 1, num_features)
                # Since each trace already represents a sequence, we treat it as a single sequence
                sequence = df_normalized[self.feature_cols].values.reshape(1, 1, len(self.feature_cols))
                
                # However, the model expects (batch_size, seq_length, features)
                # We need to reshape properly based on the model's expected input
                # The trace already contains 5 timestamps worth of data flattened
                # We need to unflatten it back to (1, 5, 5) for 5 timestamps and 5 features each
                num_features_per_timestamp = 5
                sequence = df_normalized[self.feature_cols].values.reshape(1, self.seq_length, num_features_per_timestamp)
                
                # Make prediction
                predicted_qoe_scaled = self.model.predict(sequence, verbose=0)
                
                # Inverse transform to get the actual QoE value
                # Create a dummy array with the same shape as what the scaler expects
                dummy_array = np.zeros((1, len(self.feature_cols) + 1))  # +1 for QoE column
                dummy_array[0, -1] = predicted_qoe_scaled[0, 0]  # Put prediction in QoE column
                
                # Inverse transform
                inverted = self.scaler.inverse_transform(dummy_array)
                predicted_qoe = inverted[0, -1]
                
                predictions.append(float(predicted_qoe))
                
            except Exception as e:
                print(f"Error processing trace {i}: {e}")
                predictions.append(-1)  # Return -1 for errors as in the original
        
        # Return single value if only one trace, otherwise return list
        if len(predictions) == 1:
            return predictions[0]
        else:
            return predictions