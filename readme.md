# QR Code Manager

A web application to create, manage, and track dynamic QR codes with various content types.

## Features

- User authentication (registration, login, logout)
- Dynamic QR code generation for multiple content types:
  - URLs
  - Plain text
  - Email links
  - Phone numbers
  - SMS messages
  - WiFi networks
  - vCards (contact information)
- Customizable QR code colors
- QR code tracking and analytics (view scan counts)
- QR code management (enable/disable, delete)
- Dashboard to visualize your QR codes

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB running locally on port 27017

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/qr-code-manager.git
   cd qr-code-manager
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Make sure MongoDB is running on localhost:27017

## Running the Application

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

1. Register a new account
2. Log in with your credentials
3. From the dashboard, navigate to "Manage QR Codes"
4. Create a new QR code by clicking the "Create New QR Code" button
5. Fill in the details for your QR code:
   - Name: Give your QR code a memorable name
   - Type: Select the content type (URL, text, email, etc.)
   - Content: Enter the specific content for your chosen type
   - Colors: Customize the foreground and background colors
6. Click "Generate QR Code" to create your QR code
7. Manage your QR codes from the main interface:
   - Enable/disable QR codes to control access
   - Delete QR codes you no longer need
   - View scan counts to monitor usage

## QR Code Types

- **URL**: Redirects to the specified web address
- **Text**: Displays plain text content
- **Email**: Opens email client with pre-filled fields
- **Phone**: Initiates a call to the specified number
- **SMS**: Opens messaging app with pre-filled message
- **WiFi**: Helps connect to WiFi networks
- **vCard**: Provides contact information

## Technical Details

- Backend: Flask (Python)
- Database: MongoDB
- Authentication: Session-based with bcrypt password hashing
- QR Code Generation: qrcode library
- Image Processing: Pillow (PIL Fork)

## Project Structure

```
/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── static/
│   └── styles.css          # CSS stylesheets
└── templates/
    ├── base.html           # Base template
    ├── auth/
    │   ├── login.html      # Login page
    │   └── register.html   # Registration page
    ├── dashboard/
    │   └── home.html       # Dashboard home
    └── qr/
        ├── inactive.html   # Inactive QR code page
        ├── index.html      # QR management page
        └── scan.html       # QR code display page
```

## Security Features

- Passwords are hashed using bcrypt
- QR codes are associated with user accounts
- Access control checks for all operations
- Session-based authentication

## Future Enhancements

- QR code editing
- Advanced analytics
- Custom QR code designs
- API access
- Batch QR code generation
- Export options (PDF, ZIP)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.