from abc import ABC, abstractmethod

class BaseDeepfakeDetector(ABC):
    """
    Abstract interface for deepfake and synthetic image detectors.
    Allows seamlessly swapping the baseline forensic rule engine with 
    trained PyTorch / Deep Learning classification models.
    """

    @abstractmethod
    def predict(self, image_path: str, forensic_data: dict) -> dict:
        """
        Analyze an image and its extracted forensic features to produce 
        a classification outcome, confidence score, risk score, and detected indicators.
        """
        pass
