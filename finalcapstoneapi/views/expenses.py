"""View module for handling requests about supplies"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from finalcapstoneapi.models import Expenses, Supply_Type, expenses
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
from django.db.models.aggregates import Sum
from datetime import datetime
from django.db.models.functions import ExtractMonth
import uuid
import base64
from django.core.files.base import ContentFile


class CurrentUserSerializer(serializers.ModelSerializer):
    """JSON serializer for users"""
    class Meta:
        model = User
        fields = ('id', )


class SupplyTypeSerializer(serializers.ModelSerializer):
    """JSON serializer for Supply Types"""
    class Meta:
        model = Supply_Type
        fields = ('name', 'id')


class ExpenseSerializer(serializers.ModelSerializer):
    """JSON serializer for Expense

    Arguments:
        serializers
    """
    supply_type = SupplyTypeSerializer(many=False)
    user = CurrentUserSerializer(many=False)

    class Meta:
        model = Expenses
        fields = ('id', 'user', 'cost', 'date_purchased',
                    'supply_type', 'image', 'dateExpenseConverted')


class SupplyTypeExpensesSerializer(serializers.ModelSerializer):
    """JSON serializer for expenses by supply_types"""
    class Meta:
        model = Expenses
        fields = ('supply_type_id', 'totalexpense')


class MonthExpensesSerializer(serializers.ModelSerializer):
    """JSON serializer for expenses by month"""
    class Meta:
        model = Expenses
        fields = ('totalexpense', 'expensemonth')


class Expense(ViewSet):

    def list(self, request):
        """Handle GET requests to Expense resource"""
        currentYear = datetime.now().year
        expenses = Expenses.objects.filter(
            date_purchased__contains=currentYear)
        serializer = ExpenseSerializer(
            expenses, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Handle GET request to one Expense"""

        try:
            expense = Expenses.objects.get(pk=pk)
            serializer = ExpenseSerializer(
                expense, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def create(self, request):
        """Handle POST operations for Expenses

        Returns:
            Response -- JSON serialized Expense instance
        """
        # Verify that all required keys are present in POST body
        missing_keys = self._get_missing_keys()
        if len(missing_keys) > 0:
            return Response(
                {'message':
                    f'Request body is missing the following required properties: {", ".join(missing_keys)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        expense = Expenses()

        user = User.objects.get(id=request.auth.user.id)
        expense.user = user
        expense.date_purchased = request.data["date_purchased"]
        expense.cost = request.data["cost"]
        expense.image = request.data["image"]

        # format, imgstr = request.data['image'].split(';base64,')
        # ext = format.split('/')[-1]
        # data = ContentFile(base64.b64decode(imgstr), name=f'{request.data["id"]}-{uuid.uuid4()}.{ext}')
        # expense.image = data

        supply_type = Supply_Type.objects.get(
            pk=request.data["supply_type_id"])
        expense.supply_type = supply_type

        try:
            expense.save()
            serializer = ExpenseSerializer(
                expense, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single supply type
        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            expense = Expenses.objects.get(pk=pk)
            expense.delete()
            # if succesful it will return a status code of 204
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        # if the object to be deleted doesn't exist status code will be 404
        except Expenses.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """Handle PUT operations for Expenses

        Returns:
            Response -- Empty body with 204 status code
        """

        missing_keys = self._get_missing_keys()
        if len(missing_keys) > 0:
            return Response(
                {'message':
                    f'Request body is missing the following required properties: {", ".join(missing_keys)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=request.auth.user.id)

        expense = Expenses.objects.get(pk=pk)
        expense.date_purchased = request.data["date_purchased"]
        expense.cost = request.data["cost"]
        expense.image = request.data["image"]
        expense.user = user

        supply_type = Supply_Type.objects.get(
            pk=request.data["supply_type_id"])
        expense.supply_type = supply_type

        expense.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def _get_missing_keys(self):
        """Given the request.data for a POST/PUT request, return a list containing the
        string values of all required keys that were not found in the request body"""
        REQUIRED_KEYS = [
            'date_purchased', 'cost', 'supply_type_id'
        ]

        return [key for key in REQUIRED_KEYS if not key in self.request.data]


class ExpenseBySupplyType(ViewSet):
    """Handle GET requests to Expense resource - groups Expense resource by supply types and total expense
        SQL Statement: "
        Select Sum(cost), s.name as SupplyType
        From finalcapstoneapi_expenses as e
        JOIN finalcapstoneapi_supply_type as s on e.supply_type_id = s.id
        Group By supply_type_id
        "
    """
    def list(self, request):
        user = User.objects.get(id=request.auth.user.id)
        currentYear = datetime.now().year
        #Select Sum(cost), s.name as SupplyType
        # From finalcapstoneapi_expenses as e
        # JOIN finalcapstoneapi_supply_type as s on e.supply_type_id = s.id
        # Group By supply_type_id
        supplies = Expenses.objects.values('supply_type_id').annotate(totalexpense=Sum(
            F('cost')
        )).filter(Q(user=user) & Q(date_purchased__contains=currentYear))
        serializer = SupplyTypeExpensesSerializer(
            supplies, many=True, context={'request': request})
        return Response(serializer.data)


class ExpenseByMonth(ViewSet):
    """Handle GET requests to Expense resource - groups Expense resource by supply types and total expense
        SQL Statement: "
        select strftime('%m', date_purchased) as Month, 
        sum(cost)
        from finalcapstoneapi_expenses
        where strftime('%Y', date_purchased) = strftime('%Y',date('now'))
        group by strftime('%m', date_purchased)
        order by Month;
        "
    """

    def list(self, request):
        user = User.objects.get(id=request.auth.user.id)
        currentYear = datetime.now().year
        monthexpenses = Expenses.objects.values('date_purchased__month').annotate(expensemonth=ExtractMonth(
            'date_purchased__month'), totalexpense=Sum(F('cost'))).filter(Q(user=user) & (Q(date_purchased__contains=currentYear)))
        serializer = MonthExpensesSerializer(
            monthexpenses, many=True, context={'request': request})
        return Response(serializer.data)
