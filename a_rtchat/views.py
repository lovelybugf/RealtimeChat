from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import *
from django.http import Http404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db.models import Max
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import subprocess
import json
import socket
import threading
import time
import os
import sys


@login_required
def chat_view(request, chatroom_name = "public-chat"):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:30]
    form = ChatMessageCreateForm()
    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    now = timezone.now()
    yesterday = now - timedelta(days=1)

    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            chat_group.members.add(request.user)

    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message' : message,
                'user' : request.user,
                'now' : now,
                'yesterday': yesterday,
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)
    
    # Lấy danh sách chat groups với tin nhắn mới nhất
    chat_groups = request.user.chat_groups.annotate(
        latest_message_time=Max('chat_messages__created')
    ).order_by('-latest_message_time')
            
    context = {
        'chat_messages' : chat_messages,
        'form' : form,
        'other_user' : other_user,
        'chatroom_name' : chatroom_name,
        'chat_group' : chat_group,
        'now' : now,
        'yesterday': yesterday,
        'chat_groups': chat_groups,
    }

    return render(request, 'a_rtchat/chat.html', context)

@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username = username)
    chatroom = ChatGroup.objects.filter(
        is_private=True,
        members=request.user
    ).filter(
        members=other_user
    ).first()
    if not chatroom:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(request.user, other_user)
        
    return redirect('chatroom', chatroom.group_name)

@login_required
def new_chat_group(request):
    form = NewGroupForm()
    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            chat_group = form.save(commit=False)
            chat_group.admin = request.user
            chat_group.save()
            chat_group.members.add(request.user)
            return redirect('chatroom', chat_group.group_name)
    context = {
        'form' : form,

    }
    return render(request, 'a_rtchat/create_chat_room.html', context)

@login_required
def manage_group(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    
    form = ManageGroupForm(instance=chat_group) 
    form1 = AddUserToGroupForm()
    if request.method == 'POST':
        form = ManageGroupForm(request.POST, instance=chat_group)
        form1 = AddUserToGroupForm(request.POST)
        if form.is_valid():
            form.save()
            
            remove_members = request.POST.getlist('remove_members')
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)
                messages.success(request, f'Đã xóa thành viên {member.profile.name} khỏi nhóm chat.')
                
        if form1.is_valid():
            username = form1.cleaned_data['username']
            try:
                user_to_add = User.objects.get(username=username)
                chat_group.members.add(user_to_add)
                messages.success(request, f'Đã thêm thành viên {user_to_add.profile.name} vào nhóm chat.')
            except User.DoesNotExist:
                if username:
                    messages.error(request, f'Không tìm thấy thành viên với tên người dùng: {username}')
            return redirect('manage-group', chatroom_name) 
    
    context = {
        'form' : form,
        'chat_group' : chat_group,
        'form1' : form1,
    }   
    return render(request, 'a_rtchat/manage_group.html', context) 

def chat_file_upload(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    if request.htmx and request.FILES:
        file = request.FILES['file']
        message = GroupMessage.objects.create(
            file = file,
            author = request.user, 
            body = 'sent a file',
            group = chat_group,
        )
        channel_layer = get_channel_layer()
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }
        async_to_sync(channel_layer.group_send)(
            chatroom_name, event
        )
    return HttpResponse()
@csrf_exempt
def start_Ransanmoi(request):
    if request.method == 'POST':
        print("Request body:", request.body)  # Debug
        try:
            data = json.loads(request.body)
            game_type = data.get('game_type')
            if game_type == 'snake':
                subprocess.Popen(["python3", "Game/Ransanmoi/gametest2.py"])
                return JsonResponse({"status": "success", "message": "Trò chơi Rắn Săn Mồi đã bắt đầu!"})
            return JsonResponse({"status": "error", "message": "Loại trò chơi không hợp lệ"}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({"status": "error", "message": "Dữ liệu JSON không hợp lệ: " + str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Yêu cầu không hợp lệ"}, status=400)

@csrf_exempt
def start_XO(request):
    if request.method == 'POST':
        try:
            # Kiểm tra xem server.py đã chạy chưa bằng cách thử kết nối đến port 5555
            server_running = False
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.connect(('127.0.0.1', 5555))
                test_socket.close()
                server_running = True
                print("✔ Server đã chạy.")
            except:
                print("⏳ Server chưa chạy, khởi động...")
                threading.Thread(
                    target=lambda: subprocess.Popen(
                        [sys.executable, os.path.abspath("Game/XO/server.py")]
                    ),
                    daemon=True
                ).start()
                time.sleep(2)  # đợi server khởi động

            # Dù server đã chạy hay vừa chạy, luôn mở client
            threading.Thread(
                target=lambda: subprocess.Popen(
                    [sys.executable, os.path.abspath("Game/XO/client.py")]
                ),
                daemon=True
            ).start()

            return JsonResponse({
                "status": "success",
                "message": "Đã khởi chạy client XO"
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    return JsonResponse({"status": "error", "message": "Yêu cầu không hợp lệ"}, status=400)

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
        context = {
            'users': users,
            'query': query
        }
        return render(request, 'a_rtchat/search_results.html', context)
    return HttpResponse('')