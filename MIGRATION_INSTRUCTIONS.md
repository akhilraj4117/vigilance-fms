# Database Migration Instructions

## Complaint Details - New Fields Added

The following fields have been added to the `complaint_details` table to match desktop app functionality:

- `plaintiff_designation` (VARCHAR 200)
- `plaintiff_institution` (VARCHAR 200)  
- `respondent_designation` (VARCHAR 200)
- `respondent_institution` (VARCHAR 200)

## How to Run Migration on Render.com

### Option 1: Using Render Shell
1. Go to your Render dashboard
2. Select your web service
3. Click "Shell" tab
4. Run: `python add_complaint_fields.py`

### Option 2: Automatic on Deploy
The migration script will be automatically run when the app detects the model changes and attempts to use the new fields.

### Option 3: Manual PostgreSQL
If needed, you can manually add the columns using Render's PostgreSQL dashboard:

```sql
ALTER TABLE complaint_details ADD COLUMN plaintiff_designation VARCHAR(200);
ALTER TABLE complaint_details ADD COLUMN plaintiff_institution VARCHAR(200);
ALTER TABLE complaint_details ADD COLUMN respondent_designation VARCHAR(200);
ALTER TABLE complaint_details ADD COLUMN respondent_institution VARCHAR(200);
```

## Features Added

### 1. PEN Autopopulation
- Enter PEN in plaintiff/respondent fields
- On blur (when you leave the field), employee details are automatically fetched
- Name, designation, and institution fields are auto-filled

### 2. Institution Autocomplete
- Type 2+ characters in institution field
- Get instant suggestions from database
- Uses HTML5 datalist for native browser autocomplete

## Testing

After deployment, test the following:

1. **Open Complaint Modal** on any file
2. **Enter a PEN** (e.g., employee PEN from your database)
3. **Verify** name, designation, and institution auto-populate
4. **Type in institution field** and verify autocomplete suggestions appear
5. **Save** and verify data persists correctly
6. **Reload** the modal and verify saved data loads properly

## Troubleshooting

If fields don't save:
- Check browser console for JavaScript errors
- Verify migration script ran successfully
- Check Render logs for database errors
- Confirm all 4 new columns exist in database

If autopopulation doesn't work:
- Verify employee exists with that PEN
- Check network tab to see if API call succeeds
- Ensure `/employees/api/get/<pen>` endpoint is working

If institution autocomplete doesn't show:
- Verify institutions exist in database
- Check `/institutions/api/search` endpoint
- Ensure typing 2+ characters triggers search
