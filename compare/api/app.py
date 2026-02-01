from flask import Flask, render_template, request, session, redirect, url_for, Blueprint
import secrets

TO_RANK = ["T1", "GENG", "HLE", "KT", "NS", "DK", "DNS", "BFX", "DRX", "BRO"]

compare_bp = Blueprint('compa', __name__, url_prefix='/')

@compare_bp.route('/')
def index():
    # Initialize session
    session['to_rank'] = TO_RANK
    session['wins'] = {item: 0 for item in TO_RANK}
    session['comparisons'] = []
    session['current_i'] = 0
    session['current_j'] = 1
    session['phase'] = 'pairwise'  # or 'tiebreak'

    return redirect('compare')


@compare_bp.route('/compare', methods=['GET', 'POST'])
def compare():

    if "phase" not in session:
        return redirect("/")

    if request.method == 'POST':
        choice = request.form.get('choice')

        if session['phase'] == 'pairwise':
            item1 = session['to_rank'][session['current_i']]
            item2 = session['to_rank'][session['current_j']]

            if choice == '1':
                session['wins'][item1] += 1
            elif choice == '2':
                session['wins'][item2] += 1

            # Move to next comparison
            session['current_j'] += 1
            if session['current_j'] >= len(session['to_rank']):
                session['current_i'] += 1
                session['current_j'] = session['current_i'] + 1

            # Check if pairwise comparisons are done
            if session['current_i'] >= len(session['to_rank']) - 1:
                return redirect('process_ties')

            session.modified = True
            return redirect('compare')

        elif session['phase'] == 'tiebreak':
            tied_items = session['tied_items']
            winner_idx = int(choice) - 1
            winner = tied_items[winner_idx]

            session['final_ranking'].append(winner)
            tied_items.remove(winner)

            if len(tied_items) == 1:
                session['final_ranking'].append(tied_items[0])
                # Move to next tie group
                session['tie_index'] += 1
                return redirect('process_ties')
            else:
                session['tied_items'] = tied_items
                session.modified = True
                return redirect('compare')

    # GET request - show current comparison
    if session['phase'] == 'pairwise':
        item1 = session['to_rank'][session['current_i']]
        item2 = session['to_rank'][session['current_j']]
        total = len(session['to_rank'])
        completed = len([1 for i in range(session['current_i']) for j in range(i + 1, total)]) + (
                    session['current_j'] - session['current_i'] - 1)
        total_comparisons = total * (total - 1) // 2

        return render_template('compare.html',
                               item1=item1,
                               item2=item2,
                               progress=f"{completed}/{total_comparisons}")

    elif session['phase'] == 'tiebreak':
        tied_items = session['tied_items']
        return render_template('tiebreak.html',
                               tied_items=tied_items)


@compare_bp.route('/process_ties')
def process_ties():
    if 'final_ranking' not in session:
        # First time processing ties
        wins = session['wins']
        ranked = sorted(wins.items(), key=lambda x: x[1], reverse=True)

        session['ranked'] = ranked
        session['final_ranking'] = []
        session['tie_index'] = 0
        session.modified = True

    ranked = session['ranked']
    final_ranking = session['final_ranking']

    # Find next tie group
    i = session['tie_index']

    # Skip already processed items
    while i < len(ranked):
        current_wins = ranked[i][1]
        tied_items = [ranked[i][0]]
        j = i + 1
        while j < len(ranked) and ranked[j][1] == current_wins:
            tied_items.append(ranked[j][0])
            j += 1

        if len(tied_items) > 1:
            # Found a tie, need to break it
            session['phase'] = 'tiebreak'
            session['tied_items'] = tied_items
            session['tie_index'] = i
            session.modified = True
            return redirect('compare')
        else:
            # No tie, just add to final ranking
            final_ranking.append(tied_items[0])

        i = j

    # Update session with final ranking
    session['final_ranking'] = final_ranking
    session['tie_index'] = i
    session.modified = True

    # All done!
    return redirect('results')


@compare_bp.route('/results')
def results():
    final_ranking = session.get('final_ranking', [])
    return render_template('results.html', ranking=final_ranking)