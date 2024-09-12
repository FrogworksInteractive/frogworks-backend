class Structure:
    attributes: list = []
    private_attributes: list = []

    def into_dict(self, private: bool = False) -> dict:
        self_dict: dict = {}

        from utils import Utils

        for attribute in self.attributes:
            if attribute in self.private_attributes and private:
                self_dict[attribute] = Utils.serialize(getattr(self, attribute), private)
            elif attribute not in self.private_attributes:
                self_dict[attribute] = Utils.serialize(getattr(self, attribute), private)

        return self_dict
