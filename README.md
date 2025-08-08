# Crop & Afforestation Recommendation AI Bot

## Project Overview
The Crop & Afforestation Recommendation AI Bot is a Streamlit-based Python application designed to provide intelligent recommendations for native crops and tree species suitable for urban afforestation and agriculture in India. By leveraging real-time environmental data, the bot aims to enhance biodiversity, pollution control, and sustainability in urban settings.

## Features
- **Location-Based Recommendations**: Users can input their location via PIN code or GPS to receive tailored plant and crop suggestions.
- **API Integration**: The application aggregates data from multiple APIs, including soil, weather, air quality, and biodiversity information.
- **User-Friendly Interface**: Built with Streamlit, the app offers an intuitive interface for easy interaction and clear output.
- **AI-Driven Suggestions**: Powered by the Gemini Pro API, the bot provides context-aware recommendations based on user goals and environmental conditions.

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
   - Copy `.env.example` to `.env` and fill in your API keys.

## Usage
To run the application, execute the following command:
```
streamlit run src/app.py
```
Open your web browser and navigate to `http://localhost:8501` to access the application.

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
