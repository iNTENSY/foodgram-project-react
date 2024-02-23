from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.paginations import CustomPagination
from users.models import Follow
from users.serializers import CustomUserSerializer, FollowSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            if user == author:
                return Response({
                    'errors': 'Вы не можете подписываться на самого себя'
                }, status=HTTPStatus.BAD_REQUEST)
            if Follow.objects.filter(subscriber=user, author=author).exists():
                return Response({
                    'errors': 'Вы уже подписаны на данного пользователя'
                }, status=HTTPStatus.BAD_REQUEST)
            serializer = FollowSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(subscriber=user, author=author)
            return Response(serializer.data, status=HTTPStatus.CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow,
                                             subscriber=user,
                                             author=author)
            subscription.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        query = Follow.objects.filter(subscriber=user)
        paginate = self.paginate_queryset(query)
        serializer = FollowSerializer(paginate, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)
