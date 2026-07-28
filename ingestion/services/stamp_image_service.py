from ingestion.models import StampImage


class StampImageService:
    """
    CRUD operations for StampImage entities.
    This service only interacts with the database.
    """

    def create_stamp_image(self, stamp_image: StampImage) -> StampImage:
        stamp_image.save()
        return stamp_image


    def get_stamp_image_by_id(self, image_id: int) -> StampImage:
        return StampImage.objects.get(id=image_id)


    def get_all_stamp_images(self) -> list[StampImage]:
        return list(StampImage.objects.order_by("-uploaded_at"))


    def delete_stamp_image(self, image_id: int) -> bool:
        image = StampImage.objects.get(id=image_id)

        image.file.delete(save=False)
        image.delete()

        return True
