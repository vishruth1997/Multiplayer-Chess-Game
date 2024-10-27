from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Board, Game, UserGameJournal
from .forms import ChessMoveForm, JoinForm, LoginForm, ChallengeForm, GameDescriptionForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import chess
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.sessions.models import Session
from django.utils import timezone
from collections import Counter
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse

@login_required(login_url='/login/')
def home(request):
    # Clean up expired sessions to ensure accuracy
    Session.objects.filter(expire_date__lt=timezone.now()).delete()

    # Get the logged-in user IDs from the session data
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    logged_in_user_ids = [int(session.get_decoded().get('_auth_user_id')) for session in active_sessions if session.get_decoded().get('_auth_user_id')]

    unique_user_ids = list(dict.fromkeys(logged_in_user_ids))

    # Filter users who are currently logged in and exclude the current user
    users_online = User.objects.filter(id__in=unique_user_ids).exclude(id=request.user.id)

    # Check if the user has an active game in progress
    current_game = Game.objects.filter(Q(player1=request.user) | Q(player2=request.user), active=True).first()

    if current_game:
        return redirect('game_in_progress')

    # Initialize the challenge form
    challenge_form = ChallengeForm()

    # Get the games and prefetch the user's journal entries for each game, excluding deleted ones
    game_list = Game.objects.filter(
        Q(player1=request.user) | Q(player2=request.user)
    ).exclude(deleted_by=request.user).order_by('-id').prefetch_related('usergamejournal_set')

    # Determine the outcome from the perspective of the logged-in user
    for game in game_list:
        if game.outcome:
            if request.user == game.player1:
                if "wins" in game.outcome:
                    game.user_outcome = "Win" if game.player1.username in game.outcome else "Loss"
                elif "draw" in game.outcome:
                    game.user_outcome = "Tie"
            elif request.user == game.player2:
                if "wins" in game.outcome:
                    game.user_outcome = "Win" if game.player2.username in game.outcome else "Loss"
                elif "draw" in game.outcome:
                    game.user_outcome = "Tie"
        else:
            game.user_outcome = "Ongoing"

    paginator = Paginator(game_list, 10)  # Show 10 games per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass user-specific journal entries to the template
    return render(request, 'chessboard/home.html', {
        'users_online': users_online,
        'challenge_form': challenge_form,
        'page_obj': page_obj,
        'user_journal_entries': UserGameJournal.objects.filter(user=request.user, deleted_for_user=False),  # Pass user-specific journal entries
    })


@login_required(login_url='/login/')
def game_in_progress(request):
    current_game = Game.objects.filter(Q(player1=request.user) | Q(player2=request.user), active=True).first()

    if not current_game:
        return redirect('home')

    chess_board = chess.Board(current_game.fen) if current_game.fen != 'startpos' else chess.Board()
    current_turn = 'white' if chess_board.turn else 'black'

    form = ChessMoveForm(request.POST or None)

    if request.method == 'POST':
        if 'resign' in request.POST:  # Player clicked "Resign"
            if request.user == current_game.player1:
                current_game.outcome = f'{current_game.player2.username} wins by resignation'
            else:
                current_game.outcome = f'{current_game.player1.username} wins by resignation'
            current_game.active = False  # Game is no longer active
            current_game.save()
            return redirect('home')  # Redirect to game history after resignation

        if 'move' in request.POST and form.is_valid():  # Only validate move submission
            uci_move = form.cleaned_data['uci_move']

            if (current_turn == 'white' and request.user == current_game.player1) or (current_turn == 'black' and request.user == current_game.player2):
                try:
                    chess_move = chess.Move.from_uci(uci_move)
                    if chess_move in chess_board.legal_moves:
                        chess_board.push(chess_move)
                        current_game.moves += 1
                        current_game.fen = chess_board.fen()
                        current_game.turn = 'black' if current_turn == 'white' else 'white'  # Switch the turn
                        current_game.save()
                    else:
                        form.add_error(None, 'Invalid move!')
                except ValueError:
                    form.add_error(None, 'Invalid move format!')

    page_data = load_board_from_fen(current_game.fen)
    return render(request, 'chessboard/game_in_progress.html', {
        'page_data': page_data,
        'chessboard_form': form,
        'current_game': current_game,
        'current_turn': current_turn,
    })

def load_board_from_fen(fen):
    # Check if the FEN is 'startpos' and load the default FEN
    if fen == 'startpos':
        chess_board = chess.Board()  # Start the chess board in the default position
    else:
        try:
            chess_board = chess.Board(fen)  # Load the FEN from the game model
        except ValueError as e:
            raise ValueError(f"Error loading FEN: {e}")

    page_data = {"rows": []}

    # Mapping of chess pieces to their Unicode symbols
    piece_symbols = {
        'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',  # White pieces
        'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;'   # Black pieces
    }

    for row_number in range(8, 0, -1):  # Chess rows 8 to 1
        row_data = {}
        row_data['row_number'] = row_number

        for col in 'abcdefgh':  # Columns a to h
            square_name = f"{col}{row_number}"
            square_index = chess.square(ord(col) - ord('a'), row_number - 1)  # Convert 'a1' to square index
            piece = chess_board.piece_at(square_index)
            if piece:
                piece_symbol = piece_symbols.get(piece.symbol(), '&nbsp;')  # Map to Unicode or empty
            else:
                piece_symbol = '&nbsp;'  # Empty square
            row_data[square_name] = piece_symbol

        page_data['rows'].append(row_data)

    # Handle the labels for A-H at the bottom
    row_labels = {"row_labels": {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "H": "H"}}
    page_data['rows'].append(row_labels)

    return page_data


@login_required(login_url='/login/')
def game_history(request):
    history = Game.objects.filter(Q(player1=request.user) | Q(player2=request.user))
    return render(request, 'chessboard/history.html', {'history': history})


@login_required(login_url='/login/')
def delete_game(request, game_id):
    # Get the game object by id
    game = get_object_or_404(Game, id=game_id)
    
    # Mark the journal entry as deleted for this user only
    journal_entry = get_object_or_404(UserGameJournal, user=request.user, game=game)
    journal_entry.deleted_for_user = True
    journal_entry.save()

    # Redirect back to the home page after deleting
    return redirect('home')

# Function to reset the chessboard to the initial state
def newGame(user):
    # Initialize a new chess board with the starting position
    chess_board = chess.Board()

    # Save the initial FEN position to the database for the user
    Board.objects.filter(user=user).delete()  # Clear the existing board state for the user
    Board.objects.create(user=user, fen=chess_board.fen())  # Save the starting FEN
    update_board_model(chess_board, user)

# Load the board state from the Board model into a chess.Board object
def load_chess_board_from_db(user):
    # Retrieve the latest board state for the user
    board_record = Board.objects.filter(user=user).first()
    
    if board_record and board_record.fen:
        try:
            chess_board = chess.Board(board_record.fen)  # Load the chess board from the saved FEN
        except ValueError:
            # If the FEN is invalid, reset to starting position
            chess_board = chess.Board()
            update_board_model(chess_board, user)  # Update the model with the correct FEN
    else:
        chess_board = chess.Board()  # If no record exists, initialize a new game
        update_board_model(chess_board, user)

    return chess_board

# Load the board state from the Board model for rendering
def load_board_from_db(user):
    page_data = {"rows": []}
    for row_number in range(8, 0, -1):  # Chess rows 8 to 1
        row_data = {}
        row_data['row_number'] = row_number
        
        for col in 'abcdefgh':  # Columns a to h
            square_id = f"{col}{row_number}"
            try:
                record = Board.objects.get(user=user, location=square_id)
                row_data[square_id] = record.value
            except Board.DoesNotExist:
                row_data[square_id] = "&nbsp;"  # Default to empty space if no record found
        
        # Append the row to the rows list
        page_data['rows'].append(row_data)

    # Handle the labels for A-H at the bottom
    row_labels = {"row_labels": {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "H": "H"}}
    page_data['rows'].append(row_labels)

    return page_data


# Function to update the board in the Board model after a move
def update_board_model(chess_board, user):
    # Clear the existing board for the user
    Board.objects.filter(user=user).delete()

    # Save the updated FEN to the database for the user
    Board.objects.create(user=user, fen=chess_board.fen())

    # Iterate over all squares and update the model with the pieces' positions
    for square in chess.SQUARES:
        square_name = chess.square_name(square)
        piece = chess_board.piece_at(square)
        if piece:
            # Map the piece symbol to the corresponding HTML entity
            html_entity_piece = piece_symbol_to_html_entity(piece.symbol())
            Board.objects.create(user=user, location=square_name, value=html_entity_piece)
        else:
            Board.objects.create(user=user, location=square_name, value="&nbsp;")

# Helper function to convert HTML entity to piece symbol for python-chess
def html_entity_to_piece_symbol(entity):
    pieces = {
        '&#9812;': 'K', '&#9813;': 'Q', '&#9814;': 'R', '&#9815;': 'B', '&#9816;': 'N', '&#9817;': 'P',  # White pieces
        '&#9818;': 'k', '&#9819;': 'q', '&#9820;': 'r', '&#9821;': 'b', '&#9822;': 'n', '&#9823;': 'p',  # Black pieces
    }
    return pieces.get(entity, None)

# Helper function to convert python-chess piece symbols to HTML entities
def piece_symbol_to_html_entity(piece_symbol):
    pieces = {
        'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',  # White pieces
        'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;',  # Black pieces
    }
    return pieces.get(piece_symbol, "&nbsp;")

def history(request):
    return render(request, 'chessboard/history.html')

def rules(request):
    return render(request, 'chessboard/rules.html')

def aboutme(request):
    return render(request, 'chessboard/aboutme.html')

def join(request):
    if request.method == 'POST':
        join_form = JoinForm(request.POST)
        if join_form.is_valid():
            user = join_form.save(commit=False)
            # Set and encrypt the password
            user.set_password(join_form.cleaned_data['password'])
            user.save()  # Save the user with the encrypted password
            # Redirect to login or home page after successful registration
            return redirect('/login/')  # Redirect to the login page after join
        else:
            # Form invalid, return to the form with errors
            return render(request, 'chessboard/join.html', {'join_form': join_form})
    else:
        join_form = JoinForm()
    return render(request, 'chessboard/join.html', {'join_form': join_form})


from django.contrib.sessions.models import Session
from django.utils import timezone

def user_login(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    # Kill all other sessions for this user
                    existing_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                    for session in existing_sessions:
                        if str(user.id) == session.get_decoded().get('_auth_user_id'):
                            session.delete()

                    # Log the user in
                    login(request, user)
                    return redirect('/')
                else:
                    return HttpResponse("Your account is inactive.")
            else:
                # Error message when invalid credentials are provided
                return render(request, 'chessboard/login.html', {'login_form': login_form, 'error': 'Incorrect username or password'})
    else:
        login_form = LoginForm()

    return render(request, 'chessboard/login.html', {'login_form': login_form})


@login_required(login_url='/login/')
def user_logout(request):
    # Log out the user
    logout(request)
    # Redirect to the homepage after logging out
    return redirect('/')

@login_required(login_url='/login/')
def edit_game(request, game_id):
    # Logic for editing a game goes here, for now just placeholder response
    return HttpResponse(f'Edit game {game_id}')


@login_required(login_url='/login/')
def edit_description(request, game_id):
    # Fetch the game and user's journal entry
    game = get_object_or_404(Game, id=game_id)
    user_journal, created = UserGameJournal.objects.get_or_create(user=request.user, game=game)

    if request.method == 'POST':
        form = GameDescriptionForm(request.POST, instance=user_journal)
        if form.is_valid():
            form.save()
            return redirect('home')  # After saving, redirect to home page with game history
    else:
        form = GameDescriptionForm(instance=user_journal)

    return render(request, 'chessboard/edit_description.html', {'form': form, 'game': game})


@login_required(login_url='/login/')
def delete_game(request, game_id):
    # Log to check if the view is hit
    print(f"delete_game view hit with game_id: {game_id}")
    
    if request.method == "POST":
        # Get the game object by id
        game = get_object_or_404(Game, id=game_id)

        # Try to get the journal entry, but don't throw an error if it doesn't exist
        journal_entry = UserGameJournal.objects.filter(user=request.user, game=game).first()

        if journal_entry:
            # Mark the journal entry as deleted for this user
            journal_entry.deleted_for_user = True
            journal_entry.save()
            print(f"Journal entry for game {game_id} marked as deleted for user {request.user.username}")
        else:
            # If no journal entry, just log it (or handle it if needed)
            print(f"No journal entry found for game {game_id} for user {request.user.username}")
        
        # Also mark the game as deleted for this user
        game.deleted_by.add(request.user)
        game.save()
        print(f"Game {game_id} marked as deleted for user {request.user.username}")

        # Redirect back to the home page after deleting
        return redirect('home')

    return HttpResponse("Invalid request method", status=405)


@login_required(login_url='/login/')
def delete_journal_entry(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    # Only delete the user's journal entry, not the game itself
    UserGameJournal.objects.filter(user=request.user, game=game).delete()
    
    return redirect('home')

@login_required(login_url='/login/')
def online_users_ajax(request):
    # Clean up expired sessions
    Session.objects.filter(expire_date__lt=timezone.now()).delete()

    # Get the logged-in user IDs from session data
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    logged_in_user_ids = [session.get_decoded().get('_auth_user_id') for session in active_sessions]
    unique_user_ids = list(dict.fromkeys(logged_in_user_ids))

    # Filter users who are currently logged in and exclude the current user
    users_online = User.objects.filter(id__in=unique_user_ids).exclude(id=request.user.id)

    # Return the list of online users as JSON
    online_users_list = list(users_online.values('id', 'username'))
    
    return JsonResponse({'online_users': online_users_list})


@login_required(login_url='/login/')
def get_game_state(request, game_id):
    current_game = get_object_or_404(Game, id=game_id)

    if not current_game:
        return JsonResponse({'error': 'Game not found'}, status=404)

    # Prepare the response with the current FEN and whose turn it is
    chess_board = chess.Board(current_game.fen) if current_game.fen != 'startpos' else chess.Board()
    current_turn = 'white' if chess_board.turn else 'black'

    # Convert the chess board to the necessary format for front-end rendering
    page_data = load_board_from_fen(current_game.fen)

    return JsonResponse({
        'page_data': page_data,
        'current_turn': current_turn,
        'current_game_id': current_game.id,
        'player1': current_game.player1.username,
        'player2': current_game.player2.username,
        'moves': current_game.moves,
        'active': current_game.active,  # Added active status
        'outcome': current_game.outcome,  # Optionally include outcome for user feedback
    })


@login_required(login_url='/login/')
def send_challenge_ajax(request):
    if request.method == 'POST':
        challenge_form = ChallengeForm(request.POST)
        if challenge_form.is_valid():
            opponent = challenge_form.cleaned_data['opponent']
            if opponent == request.user:
                return JsonResponse({'success': False, 'error': 'You cannot challenge yourself.'})
            # Check if the opponent is online
            active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
            logged_in_user_ids = [int(session.get_decoded().get('_auth_user_id')) for session in active_sessions if session.get_decoded().get('_auth_user_id')]
            if opponent.id in logged_in_user_ids:
                # Create a new game
                new_game = Game.objects.create(player1=request.user, player2=opponent, active=True)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Opponent is not online.'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data.'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='/login/')
def check_for_challenges(request):
    # Check if there is a Game where the user is player2, active=True, moves=0
    pending_game = Game.objects.filter(player2=request.user, active=True, moves=0).first()
    if pending_game:
        return JsonResponse({'challenge_received': True})
    else:
        return JsonResponse({'challenge_received': False})
