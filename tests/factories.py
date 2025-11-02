"""Factories for Category, Product, Cart, and CartItem models using factory_boy and SQLAlchemyModelFactory."""

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.product import Product


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory to set the SQLAlchemy session."""

    class Meta:
        """Meta class for BaseFactory."""

        abstract = True
        sqlalchemy_session = None  # Set this in your tests
        sqlalchemy_session_persistence = None


class CategoryFactory(BaseFactory):
    """Factory for the Category model."""

    class Meta:
        """Factory for the Category model."""

        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")


class ProductFactory(BaseFactory):
    """Factory for the Product model."""

    class Meta:
        """Factory for the Product model."""

        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    description = factory.Faker("sentence")
    price = factory.Faker("pyfloat", left_digits=2, right_digits=2, positive=True)
    stock = factory.Faker("pyint", min_value=1, max_value=100)
    category = factory.SubFactory(CategoryFactory)


class CartFactory(BaseFactory):
    """Factory for the Cart model."""

    class Meta:
        """Factory for the Cart model."""

        model = Cart

    @factory.post_generation
    def items(self, create, extracted):
        """Add items to the cart after creation."""
        if not create:
            return

        if extracted:
            for item in extracted:
                self.items.append(item)


class CartItemFactory(BaseFactory):
    """Factory for the CartItem model."""

    class Meta:
        """Factory for the CartItem model."""

        model = CartItem

    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("pyint", min_value=1, max_value=5)
    unit_price = factory.Faker("pyfloat", left_digits=2, right_digits=2, positive=True)
