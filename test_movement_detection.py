"""
Standalone test for movement detection functions without UI dependencies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import only the movement detection functions we need to test
def calculate_monthly_summaries(df):
    """Calculate monthly summaries for each account."""
    try:
        if not all(col in df.columns for col in ['date', 'account', 'amount']):
            return None, {'success': False, 'error': 'Required columns missing'}
        
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        df_copy['year_month'] = df_copy['date'].dt.to_period('M')
        
        monthly_summary = df_copy.groupby(['account', 'year_month']).agg({
            'amount': 'sum',
            'date': 'max'
        }).reset_index()
        
        monthly_summary['date'] = monthly_summary['year_month'].dt.start_time
        monthly_summary['year'] = monthly_summary['year_month'].dt.year
        monthly_summary['month'] = monthly_summary['year_month'].dt.month
        
        return monthly_summary, {
            'success': True,
            'accounts_processed': len(monthly_summary['account'].unique()),
            'periods_processed': len(monthly_summary['year_month'].unique()),
            'total_records': len(monthly_summary)
        }
    except Exception as e:
        return None, {'success': False, 'error': str(e)}

def calculate_mom_movements(monthly_summary):
    """Calculate month-over-month movements."""
    try:
        movements = []
        sorted_data = monthly_summary.sort_values(['account', 'date'])
        
        for account in sorted_data['account'].unique():
            account_data = sorted_data[sorted_data['account'] == account].copy()
            account_data = account_data.sort_values('date')
            
            for i in range(1, len(account_data)):
                current_row = account_data.iloc[i]
                previous_row = account_data.iloc[i-1]
                
                current_amount = current_row['amount']
                previous_amount = previous_row['amount']
                
                if previous_amount != 0:
                    pct_change = ((current_amount - previous_amount) / abs(previous_amount)) * 100
                else:
                    pct_change = 100.0 if current_amount > 0 else -100.0 if current_amount < 0 else 0.0
                
                abs_change = current_amount - previous_amount
                
                movements.append({
                    'account': account,
                    'current_period': current_row['year_month'],
                    'current_amount': current_amount,
                    'previous_amount': previous_amount,
                    'percentage_change': pct_change,
                    'absolute_change': abs_change,
                    'movement_type': 'MoM'
                })
        
        movements_df = pd.DataFrame(movements)
        return movements_df, {
            'success': True,
            'total_movements': len(movements),
            'accounts_analyzed': len(movements_df['account'].unique()) if len(movements) > 0 else 0
        }
    except Exception as e:
        return None, {'success': False, 'error': str(e)}

def apply_movement_thresholds(movements_df, mom_threshold=10.0, yoy_threshold=15.0):
    """Apply threshold-based flagging."""
    try:
        if movements_df is None or len(movements_df) == 0:
            return None, {'success': False, 'error': 'No movements to analyze'}
        
        flagged_movements = movements_df.copy()
        
        def get_significance_flag(row):
            threshold = mom_threshold if row['movement_type'] == 'MoM' else yoy_threshold
            abs_pct_change = abs(row['percentage_change'])
            
            if abs_pct_change >= threshold * 3:
                return 'Critical'
            elif abs_pct_change >= threshold * 2:
                return 'High'
            elif abs_pct_change >= threshold:
                return 'Medium'
            else:
                return 'Low'
        
        flagged_movements['significance'] = flagged_movements.apply(get_significance_flag, axis=1)
        
        significant_movements = flagged_movements[
            ((flagged_movements['movement_type'] == 'MoM') & (abs(flagged_movements['percentage_change']) >= mom_threshold)) |
            ((flagged_movements['movement_type'] == 'YoY') & (abs(flagged_movements['percentage_change']) >= yoy_threshold))
        ].copy()
        
        if len(significant_movements) > 0:
            max_abs_change = abs(significant_movements['absolute_change']).max()
            if max_abs_change > 0:
                significant_movements['abs_score'] = abs(significant_movements['absolute_change']) / max_abs_change * 100
            else:
                significant_movements['abs_score'] = 0
            
            significant_movements['materiality_score'] = (
                abs(significant_movements['percentage_change']) * 0.6 + 
                significant_movements['abs_score'] * 0.4
            )
        
        return significant_movements, {
            'success': True,
            'total_movements_analyzed': len(flagged_movements),
            'significant_movements_found': len(significant_movements),
            'mom_threshold_applied': mom_threshold,
            'yoy_threshold_applied': yoy_threshold
        }
    except Exception as e:
        return None, {'success': False, 'error': str(e)}

def test_movement_detection():
    """Test the movement detection functionality."""
    print("=== Testing Movement Detection Engine ===\n")
    
    # Test data
    test_data = pd.DataFrame({
        'date': [
            '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-30',
            '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31'
        ],
        'account': ['Sales Revenue'] * 8,
        'amount': [100000, 85000, 120000, 95000, 110000, 140000, 130000, 160000]
    })
    
    print("Test Data:")
    print(test_data)
    print("\n")
    
    # Test 1: Monthly summaries
    print("1. Testing Monthly Summaries...")
    monthly_summary, monthly_stats = calculate_monthly_summaries(test_data)
    if monthly_stats['success']:
        print(f"✅ Success: {monthly_stats['accounts_processed']} accounts, {monthly_stats['periods_processed']} periods")
        print(f"   Total records: {monthly_stats['total_records']}")
    else:
        print(f"❌ Failed: {monthly_stats['error']}")
    print()
    
    # Test 2: MoM movements
    print("2. Testing MoM Movements...")
    if monthly_summary is not None:
        mom_movements, mom_stats = calculate_mom_movements(monthly_summary)
        if mom_stats['success']:
            print(f"✅ Success: {mom_stats['total_movements']} movements detected")
            print("   Sample movements:")
            if len(mom_movements) > 0:
                for i, row in mom_movements.head(3).iterrows():
                    print(f"   - {row['account']}: {row['percentage_change']:+.1f}% change (${row['absolute_change']:+,.0f})")
        else:
            print(f"❌ Failed: {mom_stats['error']}")
    print()
    
    # Test 3: Threshold application
    print("3. Testing Threshold Application...")
    if 'mom_movements' in locals() and mom_movements is not None:
        significant_movements, threshold_stats = apply_movement_thresholds(mom_movements)
        if threshold_stats['success']:
            print(f"✅ Success: {threshold_stats['significant_movements_found']} significant movements")
            print(f"   Threshold: MoM >{threshold_stats['mom_threshold_applied']}%")
            if significant_movements is not None and len(significant_movements) > 0:
                print("   Significant movements:")
                for i, row in significant_movements.iterrows():
                    print(f"   - {row['account']}: {row['percentage_change']:+.1f}% ({row['significance']}) Score: {row['materiality_score']:.1f}")
        else:
            print(f"❌ Failed: {threshold_stats['error']}")
    print()
    
    # Test 4: Edge cases
    print("4. Testing Edge Cases...")
    edge_data = pd.DataFrame({
        'date': ['2023-01-31', '2023-02-28', '2023-03-31'],
        'account': ['Test Account'] * 3,
        'amount': [0, 0, 1000]  # Division by zero test
    })
    
    edge_monthly, _ = calculate_monthly_summaries(edge_data)
    if edge_monthly is not None:
        edge_movements, edge_stats = calculate_mom_movements(edge_monthly)
        if edge_stats['success']:
            print("✅ Edge cases handled successfully")
            if len(edge_movements) > 0:
                print(f"   Zero-division handling: {edge_movements.iloc[-1]['percentage_change']:.1f}%")
        else:
            print(f"❌ Edge case failed: {edge_stats['error']}")
    print()
    
    print("=== Movement Detection Test Complete ===")

if __name__ == '__main__':
    test_movement_detection()