# Crop Recommendation AI Bot

## Project Overview

The Crop Recommendation AI Bot is a Streamlit-based Python application designed to provide intelligent recommendations for crops suitable for agriculture in India. By leveraging real-time environmental data, the bot aims to enhance agricultural productivity, food security, and sustainable farming practices.

## Features

- **🤖 Dual AI Support**: Choose between online Gemini AI or local LM Studio models
- **📍 Location-Based Recommendations**: Users can input their location via PIN code or GPS to receive tailored plant and crop suggestions
- **🌐 API Integration**: The application aggregates data from multiple APIs, including soil, weather, air quality, and biodiversity information
- **👤 User-Friendly Interface**: Built with Streamlit, the app offers an intuitive interface for easy interaction and clear output
- **🧠 AI-Driven Suggestions**: Powered by Gemini Pro API or local models, providing context-aware recommendations based on user goals and environmental conditions
- **🏠 Privacy-Focused**: Local AI option ensures your data stays on your machine
- **⚡ Performance**: Local models can provide faster responses without internet dependency

## AI Model Options

### 🌐 Web AI (Gemini)

- Uses Google's Gemini 1.5 Flash model
- Requires internet connection
- Requires API key
- Generally provides comprehensive responses

### 🏠 Local AI (LM Studio)

- Runs entirely on your local machine
- No internet required after setup
- Complete privacy - data never leaves your device
- Customizable with your preferred models
- Recommended model: `llama-3.2-3b-crop-recommender`

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/crop_recommendation_ai.git
   cd crop_recommendation_ai
   ```

2. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env` and fill in your API keys (for Web AI option).

## Local AI Setup (LM Studio)

To use the local AI option, you need to set up LM Studio:

1. **Download and Install LM Studio**:

   - Visit [https://lmstudio.ai/](https://lmstudio.ai/)
   - Download and install LM Studio for your operating system

2. **Download a Model**:

   - Open LM Studio
   - Browse and download a suitable model (recommended: any 3B-7B parameter model)
   - For crop recommendations, models like `llama-3.2-3b` work well

3. **Start the Server**:

   ```bash
   lms server start
   ```

   Or use the GUI to start the server on `http://127.0.0.1:1234`

4. **Load a Model**:

   - In LM Studio, load your downloaded model
   - The model should appear as "loaded" in the interface

5. **Test the Connection**:
   ```bash
   python test_local_api.py
   ```

## Usage

To run the application, execute the following command:

```
streamlit run src/app.py
```

Open your web browser and navigate to `http://localhost:8501` to access the application.

### Using the Application

1. **Select AI Model**: Choose between Web AI (Gemini) or Local AI (LM Studio) in the sidebar
2. **Choose Location**: Use the interactive map or enter PIN/city manually
3. **Set Goals**: Select your objective (food crops or cash crops)
4. **Get Recommendations**: Click generate to receive AI-powered crop suggestions
5. **Follow Guides**: Implement the detailed cultivation plans provided

## API Keys

You will need to obtain API keys for the following services:

- OpenWeatherMap
- Gemini API
- SoilGrids

Make sure to add these keys to your `.env` file.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- Streamlit for the web framework.
- Various APIs for providing essential environmental data.
- The community for support and inspiration in building sustainable solutions.
