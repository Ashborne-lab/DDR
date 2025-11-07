# Testing the Application

This guide will help you verify that the application is working correctly after setup or changes.

## Quick Start Test

1. **Start the app**: `streamlit run src/app.py`
2. **Use a sample case**: Select "Sample Cases" → "Cardiovascular Case"
3. **Click "Analyze Report"**
4. **Verify**: You should see at least one drug-symptom relationship detected

If this works, the basic functionality is operational.

## Comprehensive Testing

### Test 1: Text Input

1. Go to "Quick Input" tab
2. Enter: "Patient taking ibuprofen for pain. Developed stomach pain after starting medication."
3. Analyze
4. **Expected**: Should detect ibuprofen → stomach pain as adverse relationship

### Test 2: File Upload (TXT)

1. Go to "File Upload"
2. Upload a `.txt` file with medical text
3. Analyze
4. **Expected**: Should process the file and show results

### Test 3: File Upload (PDF)

1. Go to "File Upload"
2. Upload a `.pdf` file (if PyMuPDF is installed)
3. Analyze
4. **Expected**: Should extract text from PDF and process it

**Note**: If PyMuPDF isn't installed, you'll see an error message but the app won't crash.

### Test 4: BioBERT Models

1. Check "Use BioBERT AI Models" in sidebar
2. Run an analysis
3. **Expected**: 
   - First time: Slower (downloading models)
   - Subsequent: Faster (using cached models)
   - Should find more entities than rule-based alone

**Note**: If transformers library isn't installed, checkbox will be disabled.

### Test 5: Visualizations

1. Run an analysis that finds multiple relationships
2. Go to "Visualizations" tab
3. **Expected**: Should see:
   - Relationship overview chart
   - Confidence distribution
   - Network graph
   - Entity type distribution
   - Summary table

### Test 6: Database Explorer

1. Go to "Database" tab
2. Search for "ibuprofen"
3. **Expected**: Should show drug information card with class, mechanism, known effects

### Test 7: Confidence Filtering

1. Set "Minimum Confidence" slider to 0.7
2. Run analysis
3. **Expected**: Only high-confidence relationships should appear

### Test 8: Export

1. Run an analysis
2. Scroll to bottom of results
3. Click "Download Analysis Report (CSV)"
4. **Expected**: Should download a CSV file with all findings

## Troubleshooting

**Problem**: App won't start
- **Check**: Python version (3.8+), all dependencies installed
- **Fix**: `pip install -r requirements.txt`

**Problem**: PDF upload fails
- **Check**: PyMuPDF installed
- **Fix**: `pip install PyMuPDF`

**Problem**: BioBERT models don't load
- **Check**: transformers library installed, internet connection
- **Fix**: `pip install transformers torch`

**Problem**: No relationships found
- **Check**: Text contains actual drug and symptom names
- **Fix**: Try sample cases to verify app is working

**Problem**: Visualizations don't appear
- **Check**: Analysis found relationships
- **Fix**: Run analysis first, then check Visualizations tab

## Performance Benchmarks

Expected performance on a typical machine:

- **Text Analysis** (rule-based): < 1 second
- **Text Analysis** (with BioBERT, first run): 30-60 seconds (model download)
- **Text Analysis** (with BioBERT, cached): 2-3 seconds
- **PDF Extraction**: 1-2 seconds per page
- **Visualization Rendering**: < 1 second

If performance is significantly worse, check:
- Available memory
- Internet connection (for model downloads)
- CPU usage from other processes

## Edge Cases to Test

1. **Empty text**: Should show warning, not crash
2. **Very long text**: Should process (may be slower)
3. **No drugs found**: Should show info message
4. **No symptoms found**: Should show info message
5. **Special characters**: Should handle Unicode properly
6. **Multiple languages**: Rule-based works, BioBERT may struggle

## Success Criteria

The app is working correctly if:
- ✅ All input methods work (text, file, PDF, samples)
- ✅ Relationships are detected accurately
- ✅ Visualizations render properly
- ✅ Export functions work
- ✅ Error messages are helpful (not cryptic)
- ✅ App doesn't crash on bad input

If all these pass, you're good to go!
