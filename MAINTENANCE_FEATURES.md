# Maintenance and Manual Management Features

This document explains the new features for managing appliance manuals and maintenance schedules.

## Features Overview

1. **Web Search for Manuals**: Automatically search for appliance manuals online
2. **PDF Storage**: Store user manuals as PDF files
3. **Maintenance Extraction**: Extract maintenance tasks from manual PDFs
4. **Maintenance Scheduling**: Create and manage maintenance schedules with automatic due date calculation

## How to Use

### Step 1: Add Appliance Information

When creating or editing an appliance, make sure to include:
- **Brand** (required for web search)
- **Model Number** (required for web search)
- These help the system find the correct manual online

### Step 2: Search for Manual Online

1. Go to the appliance detail page
2. Click **"🔍 Search for Manual Online"** button
3. The system will search Google for PDF manuals matching your appliance brand and model
4. If found, the manual URL will be saved

### Step 3: Download Manual

1. After a manual URL is found, click **"⬇️ Download Manual"** button
2. The PDF will be downloaded and stored in your app
3. You can view/download it anytime from the appliance detail page

### Step 4: Extract Maintenance Tasks

1. Once a manual PDF is uploaded/downloaded, click **"📋 Extract Maintenance Tasks"** button
2. The system will:
   - Extract text from the PDF
   - Search for maintenance-related information
   - Create maintenance task entries automatically
3. Tasks will include:
   - Task name
   - Description
   - Frequency (daily, weekly, monthly, etc.)
   - Marked as "extracted from manual"

### Step 5: Manage Maintenance Tasks

#### View Tasks
- See all tasks on the appliance detail page
- View all maintenance tasks across appliances: **Maintenance** menu item

#### Create Tasks Manually
1. Click **"+ Add Task"** on appliance detail page or Maintenance page
2. Fill in:
   - Appliance
   - Task name
   - Description
   - Frequency
   - Last performed date (optional)
   - Next due date (auto-calculated if last performed is set)
   - Estimated duration
   - Difficulty level
   - Parts needed
   - Instructions

#### Mark Task as Complete
1. Click **"✓ Complete"** button on any active task
2. The system will:
   - Set "last performed" to today
   - Automatically calculate next due date based on frequency

#### Edit Tasks
- Click **"View"** on any task to see details
- Click **"Edit"** to modify task information

## Maintenance Task Frequencies

- **Daily**: Task repeats every day
- **Weekly**: Task repeats every week
- **Monthly**: Task repeats every month
- **Quarterly**: Task repeats every 3 months
- **Semi-Annual**: Task repeats every 6 months
- **Annual**: Task repeats every year
- **As Needed**: No automatic scheduling
- **Custom**: Set custom interval in days

## Automatic Due Date Calculation

When you mark a task as complete or set a "last performed" date, the system automatically calculates the "next due" date based on:
- The frequency you selected
- The last performed date

## Status Indicators

- **Overdue**: Red text - task is past due date
- **Due Today**: Yellow text - task is due today
- **Upcoming**: Normal text - task is scheduled for future
- **Active/Inactive**: Green/Gray - whether task is currently active

## Manual Upload

You can also manually upload a PDF:
1. When creating/editing an appliance, use the **"Manual PDF"** field
2. Upload your PDF file
3. Then use "Extract Maintenance Tasks" to parse it

## Tips

1. **Better Search Results**: Include both brand and model number for best results
2. **Manual Extraction**: The extraction works best with text-based PDFs (not scanned images)
3. **Review Extracted Tasks**: Always review automatically extracted tasks and edit as needed
4. **Custom Instructions**: Add detailed instructions and parts needed for each task
5. **Track Completion**: Regularly mark tasks as complete to keep schedules accurate

## Technical Notes

- PDF text extraction uses `pdfplumber` and `PyPDF2` libraries
- Web search uses Google search (may be rate-limited)
- Maintenance extraction uses pattern matching and can be enhanced with AI (OpenAI API key optional)
- All PDFs are stored in `media/manuals/` directory
- Maintenance tasks are linked to appliances and can be filtered by appliance

## Troubleshooting

### Manual Not Found
- Try different search terms
- Manually upload the PDF if you have it
- Check that brand and model number are correct

### Extraction Returns No Tasks
- PDF might be scanned (image-based) - needs OCR
- Manual might not contain maintenance information
- Try manually creating tasks based on the manual

### Due Dates Not Calculating
- Make sure "last performed" date is set
- Check that frequency is set correctly
- Verify `python-dateutil` package is installed

