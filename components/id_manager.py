# id_manager.py
class IDManager:
    def __init__(self):
        self._id_counter = 0
        # Optionally track 'released' IDs if you want reuse, or 
        # just keep going up. Reuse can cause complications.

    def get_new_id(self):
        """Get a brand new unique ID."""
        self._id_counter += 1
        return self._id_counter

    def reset(self):
        """Reset the counter to zero (useful for testing)."""
        self._id_counter = 0

    # If you do want to implement ID releasing or reusing logic,
    # you need to track which IDs are in use or not. 
    # It's often simpler to just never reuse IDs.
    
    def release_id(self, id_val: int):
        """
        Potentially mark 'id_val' as free. 
        If reusing IDs is needed, implement that logic here.
        """
        # For demonstration, we'll just do nothing or raise NotImplementedError
        # because reusing IDs can be complicated:
        raise NotImplementedError("ID reuse not implemented yet.")
