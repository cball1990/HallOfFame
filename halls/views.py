from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from .models import Hall, Video
from .forms import VideoForm, SearchForm
from django.forms import formset_factory
from django.http import Http404, JsonResponse 
from decouple import config
import urllib
import requests
from django.forms.utils import ErrorList


YOUTUBE_API_KEY = config('YOUTUBE_API_KEY')

def home(request):
    return render(request, ('halls/home.html'))

def dashboard(request):
    halls = Hall.objects.filter(user=request.user)
    return render(request, 'halls/dashboard.html', {'halls':halls})

def add_video(request, pk):
    form = VideoForm()
    search_form = SearchForm()
    hall = Hall.objects.get(pk=pk)
    if not hall.user == request.user:
        raise Http404
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            video = Video()
            video.hall = hall
            video.url = form.cleaned_data['url']
                #use urllib to parse the video.url from the form data
            parsed_url = urllib.parse.urlparse(video.url)
                # use urllib to query the url to get what v is equal to to give the video id example url https://www.youtube.com/watch?v=2yYsmzeVHaM&ab_channel=Let%27sGameItOut
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
                #checks to see if video id is correct then fills out details
            if video_id:
                #video_id returns a list so we need the 0 position
                video.youtube_id =  video_id[0]
                #use requests libruary so go to the API url with my api key and video_id to get the title of the video
                response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics&id={ video_id[0] }&key= { YOUTUBE_API_KEY }')
                json = response.json() 
                title = json['items'][0]['snippet']['title']
                video.title = title
                video.save()
                return redirect('detail_hall', pk)
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('Needs To Be A YouTube URL')
    return render(request,'halls/add_video.html', {'form':form, 'search_form':search_form, 'hall':hall})

#pass in a dict for the ajax function from the SearchForm
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=6&q={ encoded_search_term }&key={ YOUTUBE_API_KEY }')
        return JsonResponse(response.json())
    return JsonResponse({'error':'Not able To Validate Form'})

class DeleteVideo(generic.DeleteView):
    model = Video
    template_name = 'halls/delete_video.html'
    success_url =  reverse_lazy('dashboard')

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'
    #signs the user in after signing up
    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view

class CreateHall(generic.CreateView):
    model = Hall
    fields = ['title']
    template_name = 'halls/create_hall.html'
    success_url =  reverse_lazy('dashboard')
    #adds the current user to the Hall model
    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateHall, self).form_valid(form)
        return redirect('home')

class DetailHall(generic.DetailView):
    model = Hall
    template_name = 'halls/detail_hall.html'

class UpdateHall(generic.UpdateView):
    model = Hall
    template_name = 'halls/update_hall.html'
    fields = ['title']
    success_url =  reverse_lazy('dashboard')

class DeleteHall(generic.DeleteView):
    model = Hall
    template_name = 'halls/delete_hall.html'
    success_url =  reverse_lazy('dashboard')