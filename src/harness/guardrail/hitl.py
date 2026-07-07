from harness.core.action import Action


class HITLPipeline:

    MAX_RETRIES = 3

    @classmethod
    def prompt(cls, action: Action) -> bool:
        """
        Present a dangerous action to the user for approval.
        Returns True if approved, False if denied.
        Default is False (safety-first).
        """
        print(f"\n⚠️  DANGEROUS OPERATION DETECTED")
        print(f"   Action: {action.describe()}")
        print(f"   Rationale: {action.rationale}")
        print(f"\n   Allow this operation?")

        for attempt in range(cls.MAX_RETRIES):
            response = input("   Allow? [y/N]: ").strip().lower()
            if response == "y":
                return True
            elif response == "n" or response == "":
                return False
            else:
                remaining = cls.MAX_RETRIES - attempt - 1
                if remaining > 0:
                    print(f"   Invalid input. Please enter 'y' or 'n'. ({remaining} tries left)")
                else:
                    print("   Max retries exceeded. Operation denied.")
                    return False

        return False  # safety default
