# Crime Detection Using YOLOv8

A real-time crime detection system that uses YOLOv8 for detecting violent activities and wanted individuals using computer vision and machine learning techniques.

## Features

- Real-time violence detection using YOLOv8
- Facial recognition for identifying wanted individuals
- Automatic alerts and notifications
- Location tracking for incidents
- Web-based dashboard for monitoring
- Email notifications for administrators
- MongoDB integration for data persistence

## Tech Stack

Uses Flask, OpenCV, YOLOv8, MongoDB, and Python.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- MongoDB (local or cloud instance)
- YOLOv8 model files

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/sumit-b-freelancer/crime_detection_using_YOLOv8.git
cd crime_detection_using_YOLOv8
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following:
```env
SECRET_KEY=your_secret_key
MONGO_URI=your_mongodb_connection_string
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
MAPBOX_TOKEN=your_mapbox_token
```

5. Run the application:
```bash
python app.py
```

### Option 2: Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`.

## Configuration

### YOLO Model
Ensure you have the YOLOv8 model files in the `model.py` file. The system expects a model that can detect violence-related activities.

### Database
Configure your MongoDB connection in the `.env` file. The application expects collections for:
- `users` - for user authentication
- `complaints` - for criminal records
- `violence_detections` - for violence incident logs

### Email Notifications
The system sends email notifications when crimes are detected. Configure your email settings in the `.env` file.

## Usage

1. Register as a user or log in as an administrator
2. Add criminal profiles to the database with photos
3. Start the detection system
4. Monitor the dashboard for alerts and incidents
5. Review recorded incidents and take appropriate action

## Security Considerations

- Never commit sensitive credentials to the repository
- Use environment variables for all secrets
- Run the application with non-root user in production
- Regularly update dependencies
- Use HTTPS in production deployments

## Project Structure

```
crime_detection_using_YOLOv8/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── extensions.py         # Flask extensions
├── detector.py           # Facial recognition detection
├── violence_detect.py    # Violence detection module
├── model.py              # ML model interface
├── routes/               # Flask route blueprints
├── templates/            # HTML templates
├── static/               # CSS, JS, and image files
├── models/               # Data models
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or inquiries, contact sumitbadake@gmail.com

---

⚠️ **Legal Notice**: This system should be used in compliance with local laws and regulations regarding surveillance and privacy. Ensure proper consent and legal authorization before deploying.