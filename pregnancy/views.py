from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer, OpenApiParameter
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from json.decoder import JSONDecodeError
from .serializers import InformationSerializer, FAQSerializer
from django.db.models import Q
from .models import FAQ, Information
from user.serializers import ProfileSerializer
from user.models import Profile
import pandas as pd


# Create your views here.

class FAQUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "파일이 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 확장자에 따라 pandas로 파일 읽기
        if file.name.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            data = pd.read_excel(file)
        else:
            return Response({"error": "지원되지 않는 파일 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 데이터 저장
        faqs = []
        for _, row in data.iterrows():
            faqs.append(FAQ(
                question = row.iloc[0],
                real_question = row.iloc[1],
                answer = row.iloc[2],
                views = 0
            ))
        
        FAQ.objects.bulk_create(faqs)

        return Response({"message": "데이터가 성공적으로 업로드되었습니다."}, status=status.HTTP_201_CREATED)
    

class InfomationUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "파일이 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 확장자에 따라 pandas로 파일 읽기
        if file.name.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            data = pd.read_excel(file)
        else:
            return Response({"error": "지원되지 않는 파일 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 데이터 저장
        informations = []
        for _, row in data.iterrows():
            informations.append(Information(
                step = row.iloc[0],
                Week = row.iloc[1],
                fetus = row.iloc[2],
                maternity = row.iloc[3],
                summary = row.iloc[4]
            ))
        
        Information.objects.bulk_create(informations)

        return Response({"message": "데이터가 성공적으로 업로드되었습니다."}, status=status.HTTP_201_CREATED)