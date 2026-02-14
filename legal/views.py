from django.shortcuts import render


def cgv_view(request):
    return render(request, 'legal/cgv.html')


def privacy_view(request):
    return render(request, 'legal/privacy.html')


def mentions_view(request):
    return render(request, 'legal/mentions.html')


def escrow_guide_view(request):
    return render(request, 'legal/escrow_guide.html')