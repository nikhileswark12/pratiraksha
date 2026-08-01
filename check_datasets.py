
import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

folders_to_check = ['datasets', 'ml', 'data']

for folder in folders_to_check:
    if not os.path.exists(folder):
        print(f'Folder missing: {folder}/')
        continue
    
    print(f'\n--- Inventory for {folder}/ ---')
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.csv') or file.endswith('.parquet'):
                filepath = os.path.join(root, file)
                try:
                    if file.endswith('.csv'):
                        df = pd.read_csv(filepath, low_memory=False)
                    else:
                        df = pd.read_parquet(filepath)
                    
                    rows = len(df)
                    cols = list(df.columns)
                    cols_str = ', '.join(cols[:5])
                    
                    # Try to find date range
                    date_col = next((c for c in cols if 'date' in c.lower() or 'time' in c.lower()), None)
                    date_range = 'N/A'
                    if date_col:
                        try:
                            dates = pd.to_datetime(df[date_col].dropna())
                            if not dates.empty:
                                date_range = f'{dates.min()} to {dates.max()}'
                        except:
                            pass
                            
                    # Try to find city/location coverage
                    loc_col = next((c for c in cols if c.lower() in ['city', 'station', 'location', 'hospital_id']), None)
                    coverage = 'N/A'
                    if loc_col:
                        unique_locs = df[loc_col].nunique()
                        coverage = f'{unique_locs} unique locations'
                        # if few, list them
                        if unique_locs < 5:
                            coverage += f' ({list(df[loc_col].unique())})'
                    
                    print(f'\nFile: {filepath}')
                    print(f'  Rows: {rows}')
                    print(f'  Columns: {len(cols)} ({cols_str}...)')
                    print(f'  Date Range: {date_range} (via {date_col})')
                    print(f'  Location Coverage: {coverage} (via {loc_col})')
                    
                except Exception as e:
                    print(f'\nFile: {filepath}')
                    print(f'  Error reading file: {e}')

