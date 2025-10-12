# Facebook Number Checker - GUI Version

A modern, user-friendly GUI application for checking Facebook phone numbers.

## Features

- **Modern GUI Interface**: Clean, dark-themed interface built with CustomTkinter
- **Easy Input**: Paste phone numbers (one per line) into the text area
- **Concurrent Processing**: Configure the number of workers for parallel checking
- **Real-time Results**: Live updates showing success/failed numbers
- **Detailed Logging**: View detailed logs of all operations
- **Success Tracking**: Only counts numbers that reach the verification code page

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Running the GUI

Simply run the GUI application:
```bash
python gui.py
```

### How to Use

1. **Enter Phone Numbers**: 
   - Paste or type phone numbers in the left text area
   - One phone number per line
   - Example:
     ```
     2250708139166
     2250708135432
     2250708136329
     ```

2. **Set Concurrent Workers**:
   - Enter the number of concurrent workers (1-20)
   - Default: 5 workers
   - More workers = faster processing (but more resource intensive)

3. **Click "Start Checking"**:
   - The application will begin processing
   - You can see real-time progress in the results section

4. **View Results**:
   - **Successful Numbers Tab**: Shows phone numbers that reached the verification code page
   - **Failed Numbers Tab**: Shows numbers that failed with error messages
   - **Log Tab**: Detailed log of all operations
   - **Statistics**: See Total/Success/Failed counts at the top

5. **Stop Processing** (optional):
   - Click "Stop Checking" to halt processing
   - Currently running tasks will finish first

## Success Criteria

A phone number is marked as **successful** ONLY if it:
- Successfully reaches the Facebook verification code input page
- This means Facebook can send a verification code to that number

## Running the Old CLI Version

If you prefer the command-line version:
```bash
python main.py
```

## Notes

- The application runs Chrome in headless mode (no visible browser)
- Each check may take several seconds depending on Facebook's response time
- Successful numbers are those that can receive verification codes

