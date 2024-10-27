"""
URL configuration for project2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from chessboard import views as chessboard_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", chessboard_view.home, name='home'),
    path('history/', chessboard_view.history, name='history'),
    path('rules/', chessboard_view.rules, name='rules'),
    path('aboutme/', chessboard_view.aboutme, name='aboutme'),
    path('join/', chessboard_view.join, name='join'),
    path('login/', chessboard_view.user_login, name='login'),
    path('logout/', chessboard_view.user_logout, name='logout'),
    path('game-in-progress/', chessboard_view.game_in_progress, name='game_in_progress'),
    path('game-history/', chessboard_view.game_history, name='game_history'),
    path('delete-game/<int:game_id>/', chessboard_view.delete_game, name='delete_game'),
    path('edit_description/<int:game_id>/', chessboard_view.edit_description, name='edit_description'),
    # New URL pattern for deleting journal entry
    # path('delete-journal-entry/<int:game_id>/', chessboard_view.delete_journal_entry, name='delete_journal_entry'),
    path('delete-game/<int:game_id>/', chessboard_view.delete_game, name='delete_game'), 
    path('online-users-ajax/', chessboard_view.online_users_ajax, name='online_users_ajax'),
    path('get-game-state/<int:game_id>/', chessboard_view.get_game_state, name='get_game_state'),
    path('send-challenge-ajax/', chessboard_view.send_challenge_ajax, name='send_challenge_ajax'),
    path('check-for-challenges/', chessboard_view.check_for_challenges, name='check_for_challenges'),
]