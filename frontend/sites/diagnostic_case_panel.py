from flask import Blueprint, render_template, request, redirect, url_for

diagnostic_case_panel = Blueprint('diagnostic_case_panel', __name__)

@diagnostic_case_panel.route('/', methods=['GET', 'POST'])
def diagnostic_page():
    if request.method == 'POST':
        case_input = request.form.get('case_input')  # Get the input value
        # Add your processing logic here, e.g., saving to the database
        print(f"Diagnostic case input received: {case_input}")
        #return redirect(url_for('diagnostic_case_panel.diagnostic_page'))  # Redirect to avoid form resubmission

    return render_template('diagnostic_case_panel.html')
