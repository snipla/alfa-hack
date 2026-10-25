import numpy as np
import pandas as pd
import catboost

def generate_loan_recommendations(model: catboost.CatBoostClassifier, user_data_df: pd.DataFrame, predict_function):
    '''
    model - модель
    user_data_df - информация о заемщике в виде pandas dataframe
    predict_function(model, user_data_df) - функция, возвращающая результат выдачи кредита (одобрение/отказ)
    '''

    log_amount = float(user_data_df['loan_amount_rub'].iloc[0])
    log_term = float(user_data_df['loan_term_months'].iloc[0])
    
    real_amount = np.expm1(log_amount)
    real_term = np.expm1(log_term)

    recommendations = []
    standard_terms = (24, 36, 60, 84, 96, 120, 180, 240, 300)

    test_df = user_data_df.copy()


    # стратегия 1: уменьшаем сумму кредита
    for coeff in np.arange(0.9, 0.45, -0.05):
        new_amount = real_amount * coeff
        target_log_amount = np.log1p(new_amount)

        test_df.at[test_df.index[0], 'loan_amount_rub'] = target_log_amount
        if predict_function(model, test_df) == 1:
            recommendations.append({
                'type': 'amount_reduction',
                'text': f'Снизьте сумму кредита до {round(new_amount, 2)} руб. (сейчас {real_amount})',
                'new_log_amount': target_log_amount,
                'new_log_term': log_term
            })
            break


    # стратегия 2: увеличиваем срок кредита
    test_df.at[test_df.index[0], 'loan_amount_rub'] = log_amount
    available_terms = [t for t in standard_terms if t > real_term]
    
    for term in available_terms:
        target_log_term = np.log1p(term)
        test_df.at[test_df.index[0], 'loan_term_months'] = target_log_term

        if predict_function(model, test_df) == 1:
            recommendations.append({
                'type': 'term_extension',
                'text': f'Увеличьте срок кредита до {term} месяцев (сейчас {round(real_term)} мес)',
                'new_log_amount': log_amount,
                'new_log_term': target_log_term
            })
            break


    # стратегия 3: снижение суммы с одновременным увеличением срока
    best_combo = None
    max_money_retained = 0
    amount_coeffs = np.arange(0.95, 0.45, -0.05)

    for term in available_terms:
        target_log_term = np.log1p(term)
        test_df.at[test_df.index[0], 'loan_term_months'] = target_log_term

        for coeff in amount_coeffs:
            test_amount = real_amount * coeff
            if test_amount <= max_money_retained:
                break
            
            target_log_amount = np.log1p(test_amount)
            test_df.at[test_df.index[0], 'loan_amount_rub'] = target_log_amount

            if predict_function(model, test_df) == 1:
                max_money_retained = test_amount
                best_combo = {
                    'type': 'combo',
                    'text': f'Модифицируйте заявку следующим образом: сумма {round(test_amount, 2)} руб. и срок {term} месяцев',
                    'new_log_amount': target_log_amount,
                    'new_log_term': target_log_term
                }
                break

    if best_combo:
        recommendations.append(best_combo)

    return recommendations if recommendations else [{
        'type': None,
        'text': 'Рекомендуем сильно изменять данные в заявке на кредит, сейчас мы не можем вам предложить ни один из вариантов',
        'new_log_amount': None,
        'new_log_term': None
    }]
