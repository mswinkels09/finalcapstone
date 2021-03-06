from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework import status
from finalcapstoneapi.models import Item
from finalcapstoneapi.views.listeditems import CategorySerializer, WeightTypeSerializer, ListingTypeSerializer, UserSerializer
from django.db.models import F
from django.db.models import Q
from django.db.models.aggregates import Count
from datetime import datetime
from django.db.models.functions import ExtractMonth

class SoldItemSerializer(serializers.ModelSerializer):
    """JSON serializer for sold items"""
    user = UserSerializer(many=False)
    category = CategorySerializer(many=False)
    listing_type = ListingTypeSerializer(many=False)
    weight_type = WeightTypeSerializer(many=False)

    class Meta:
        model = Item
        fields = ('id', 'user', 'title', 'unique_item_id', 'category', 'listing_type',
                'item_weight', 'weight_type', 'notes', 'item_cost','date_listed', 
                'listing_fee', 'shipping_cost', 'shipping_paid', 'item_paid', 
                'final_value_fee', 'sold_date', 'returned', 'profit_per_item', 'profit_per_item_percentage', 'dateSoldConverted')
        depth = 1

class SoldItemsPerMonthSerializer(serializers.ModelSerializer):
    """JSON serializer for number of sold items by month"""
    class Meta:
        model = Item
        fields = ('totalitems', 'soldItemMonth')


class SoldItems(ViewSet):
    """Request handlers for sold items"""
    def list(self, request):
        """
        @api {GET} /solditems GET all sold items

        @apiSuccess (200) {Object[]} items Array of items
        @apiSuccessExample {json} Success
            [
                {
                    "id": 101,
                    "user_id": 1,
                    "title": "12 inch Baby Yoda The Mandalorian Master Stuffed Doll Plush Toys Black Friday US SAL",
                    "unique_item_id": 264954766269,
                    "category_id": {
                        "name": "Toys"
                    },
                    "listing_type_id": {
                        "name": "Ebay: Buy It Now"
                    },
                    "item_weight": 165,
                    "weight_type_id": {
                        "type": "N/A",
                        "percentage": 1
                    },
                    "notes": "great sell",
                    "item_cost": 2,
                    "date_listed": "2020-12-09",
                    "listing_fee": 0.30,
                    "shipping_cost": 8.50,
                    "shipping_paid": 12,
                    "item_paid": 15,
                    "final_value_fee": 1,
                    "sold_date": "2020-12-12",
                    "returned": "False"
                }
            ]
        """

        user = User.objects.get(id=request.auth.user.id)
        try:
            solditems = Item.objects.filter(user=user, sold_date__isnull=False)
            json_items = SoldItemSerializer(
                solditems, many=True, context={'request': request})
            return Response(json_items.data)
        except Item.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        """
        @api {GET} /solditems/:id GET sold_item

        @apiParam {id} id Item Id

        @apiSuccess (200) {Object{}} sold_item object
        @apiSuccessExample {json} Success
            {
                "id": 101,
                "user_id": 1,
                "title": "12 inch Baby Yoda The Mandalorian Master Stuffed Doll Plush Toys Black Friday US SAL",
                "unique_item_id": 264954766269,
                "category_id": {
                    "name": "Toys"
                },
                "listing_type_id": {
                    "name": "Ebay: Buy It Now"
                },
                "item_weight": 165,
                "weight_type_id": {
                    "type": "N/A",
                    "percentage": 1
                },
                "notes": "great sell",
                "item_cost": 2,
                "date_listed": "2020-12-09",
                "listing_fee": 0.30,
                "shipping_cost": 8.50,
                "shipping_paid": 12,
                "item_paid": 15,
                "final_value_fee": 1,
                "sold_date": "2020-12-12",
                "returned": "False"
            }
        """
        try:
            # pk is a parameter to this function, and 
            # Django parses it from the URL rouote parameter
            # http://localhost:8000/items/2
            #
            # The `2` at the end of the route becomes `pk`
            user = User.objects.get(id=request.auth.user.id)
            item = Item.objects.get(pk=pk, user=user, sold_date__isnull=False)
            serializer = SoldItemSerializer(item, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def update(self, request, pk=None):
        """
        @api {PUT} /solditems/:id PUT update listed item

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token fa2eba9be8282d595c997ee5cd49f2ed31f65be1

        @apiParam {id} id Listed Id route parameter
        @apiParam {Number} user_id - Current user that is authenticated
        @apiParam {String} title - Name of the item being listed
        @apiParam {Number} unique_item_id - Form of id given from the website where the user is listing the item
        @apiParam {Number} category_id - Category of item
        @apiParam {Number} listing_type_id - What kind of listing is the user using to sell the item
        @apiParam {Number} item_weight - How much the item weighs
        @apiParam {Number} weight_type_id - Id that corresponds to a percentage that will help calculate the cost of the item(if applicable)
        @apiParam {Number} item_cost - How much the item cost to buy initially (sometimes calculated using weight_type)
        @apiParam {String} date_listed - When the user listed the item
        @apiParam {Number} listing_fee - How much did it cost to list the item(if applicable)
        **only below is able to be edited** 
        @apiParam {String} notes - Any notes that the user wants to keep track of
        @apiSuccess {Number} item.shipping_cost - How must the user paid for shipping
        @apiSuccess {Number} item.shipping_paid - How much the customer paid for shipping
        @apiSuccess {Number} item.item_paid - How much the customer paid for the item
        @apiSuccess {Number} item.final_value_fee - Percentage of profit the website took out as a charge for selling an item on their website (if applicable)
        @apiSuccess {Date} item.sold_date - Date item was sold
        @apiSuccess {Boolean} item.returned - Changes to True if item was ever returned back to the user
        @apiParamExample {json} Input
            {
                "id": 101,
                "user_id": 1,
                "title": "12 inch Baby Yoda The Mandalorian Master Stuffed Doll Plush Toys Black Friday US SAL",
                "unique_item_id": 264954766269,
                "category_id": {
                    "name": "Toys"
                },
                "listing_type_id": {
                    "name": "Ebay: Buy It Now"
                },
                "item_weight": 165,
                "weight_type_id": {
                    "type": "N/A",
                    "percentage": 1
                },
                "notes": "great sell",
                "item_cost": 2,
                "date_listed": "2020-12-09",
                "listing_fee": 0.30,
                "shipping_cost": 8.50,
                "shipping_paid": 15,
                "item_paid": 15,
                "final_value_fee": 1,
                "sold_date": "2020-12-12",
                "returned": "False"
            }

        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """

        user = User.objects.get(id=request.auth.user.id)

        sold_item = Item.objects.get(pk=pk)
        try:
            if len(request.data) == 7:
                sold_item.notes = None
            else:
                sold_item.notes = request.data["notes"]
            sold_item.shipping_cost = request.data['shipping_cost']
            sold_item.shipping_paid = request.data['shipping_paid']
            sold_item.item_paid = request.data['item_paid']
            sold_item.final_value_fee = request.data['final_value_fee'] 
            sold_item.sold_date = request.data['sold_date'] 
            sold_item.returned = request.data['returned'] #stretch goal
            sold_item.user = user

            sold_item.save()

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except Exception as ex:
            return Response({'Cannot edit those areas'}) #not doing what I wish it would do

    def destroy(self, request, pk=None):
        """
        @api {DELETE} /solditems/:id DELETE line item from cart

        @apiParam {id} id Item Id to remove from cart
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        try:
            sold_item = Item.objects.get(pk=pk, sold_date__isnull=False)
            sold_item.delete()
            #if succesful it will return a status code of 204
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        #if the object to be deleted doesn't exist status code will be 404
        except Item.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_missing_keys(self):
        """Given the request.data for a POST/PUT request, return a list containing the
        string values of all required keys that were not found in the request body"""
        REQUIRED_KEYS = [
            'shipping_cost', 'shipping_paid', 'item_paid', 'final_value_fee', 'sold_date'
        ]

class SoldItemsByMonth(ViewSet):
    """Handle GET requests to Item resource - groups Item resource by month and total number of sold items
        SQL Statement: "
            select strftime('%m', sold_date) as Month, 
            Count(id)
            from finalcapstoneapi_item
            where strftime('%Y', sold_date) = strftime('%Y',date('now'))
            group by strftime('%m', sold_date)
            order by Month;
        "
    """
    def list(self, request):
        user = User.objects.get(id=request.auth.user.id)
        currentYear = datetime.now().year
        SoldItemsPerMonth = Item.objects.values('sold_date__month').annotate(soldItemMonth=ExtractMonth(
            'sold_date__month'), totalitems=Count(F('id'))).filter(Q(user=user) & (Q(sold_date__contains=currentYear)))
        serializer = SoldItemsPerMonthSerializer(
            SoldItemsPerMonth, many=True, context={'request': request})
        return Response(serializer.data)



