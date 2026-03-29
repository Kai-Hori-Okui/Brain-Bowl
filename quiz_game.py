import random
import time
import sys
import threading
import termios
from pathlib import Path
from pynput import keyboard


class QuizGame:
    def __init__(self, data_file, delay_between_facts=2.0):
        """
        Initialize the quiz game.
        
        Args:
            data_file: Path to the text file containing subject data
            delay_between_facts: Seconds between displaying each fact (default: 2.0)
        """
        self.data_file = data_file
        self.delay = delay_between_facts
        self.subjects = self.load_data()
        self.score = 0
        self.total_questions = 0
        
    def load_data(self):
        """Load and parse the data file."""
        subjects = {}
        
        with open(self.data_file, 'r') as f:
            lines = f.readlines()
        
        current_subject = None
        facts = []
        
        for line in lines:
            line = line.rstrip('\n')
            
            # Skip empty lines
            if not line.strip():
                if current_subject and facts:
                    subjects[current_subject] = facts
                    facts = []
                continue
            
            # Check if line starts with a bullet point
            if line.strip().startswith('-'):
                fact = line.strip()[1:].strip()  # Remove '-' and whitespace
                facts.append(fact)
            else:
                # This is a subject name
                if current_subject and facts:
                    subjects[current_subject] = facts
                    facts = []
                current_subject = line.strip()
        
        # Don't forget the last subject
        if current_subject and facts:
            subjects[current_subject] = facts
        
        return subjects
    
    def get_last_name(self, full_name):
        """Extract the last name from a full name."""
        return full_name.strip().split()[-1]
    
    def format_text(self, text):
        """Format text with ANSI codes for bold and italic hints.
        
        Supports:
        - **text** for bold
        - *text* for italic
        """
        import re
        
        # Replace **bold** with ANSI bold codes
        text = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', text)
        
        # Replace *italic* with ANSI italic codes
        text = re.sub(r'\*(.*?)\*', r'\033[3m\1\033[0m', text)
        
        return text
    
    def play_round(self):
        """Play a single round of the quiz."""
        if not self.subjects:
            print("No subjects loaded. Check your data file.")
            return False
        
        # Pick a random subject
        subject = random.choice(list(self.subjects.keys()))
        facts = self.subjects[subject].copy()
        random.shuffle(facts)  # Randomize the order of facts
        last_name = self.get_last_name(subject)
        
        print("\n" + "="*50)
        print("Press SPACE to stop the facts and make your guess")
        print("="*50 + "\n")
        
        facts_shown = 0
        key_pressed = threading.Event()
        
        def on_press(key):
            """Callback when a key is pressed."""
            try:
                if key == keyboard.Key.space:
                    key_pressed.set()
            except AttributeError:
                pass
        
        # Start the keyboard listener
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        try:
            # Display facts with delay, stopping if key is pressed
            for i, fact in enumerate(facts):
                if key_pressed.is_set():
                    break
                
                print(f"Fact {i+1}: {self.format_text(fact)}")
                facts_shown += 1
                
                # Wait for delay or until key is pressed
                if i < len(facts) - 1:
                    key_pressed.wait(timeout=self.delay)
                    if key_pressed.is_set():
                        break
        finally:
            listener.stop()

        # clear any buffered keystrokes before showing guess prompt
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
        
        print("\n" + "-"*50)
        
        # Get the guess
        guess = input(f"\nWho is this (last name or full name)? ").strip()
        
        # Calculate score
        # More points if they guess with fewer facts shown
        points = max(0, (len(facts) - facts_shown + 1) * 10)
        
        # Check answer
        guess_words = guess.lower().split()
        
        if len(guess_words) == 1:
            # Last name only provided - check against last name
            is_correct = guess.lower() == last_name.lower()
        else:
            # Full name provided - must match exactly
            is_correct = guess.lower() == subject.lower()
        
        if is_correct:
            print(f"\n✓ Correct! It was {subject}!")
            print(f"Points earned: {points}")
            self.score += points
        else:
            print(f"\n✗ Incorrect. The answer was {subject}.")
            print(f"Points earned: 0")
        
        self.total_questions += 1
        return True
    
    def play_interactive(self):
        """Play multiple rounds with interactive prompts."""
        print("Welcome to the Quiz Game!")
        print(f"Loaded {len(self.subjects)} subjects.")
        print(f"Displaying facts every {self.delay} second(s).\n")
        
        try:
            while True:
                self.play_round()
                
                print(f"\nCurrent Score: {self.score} points")
                print(f"Questions Answered: {self.total_questions}")

                # flush any pending keystrokes so they don't echo after exit
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
                time.sleep(1)  # Brief pause before next round
        except KeyboardInterrupt:
            print("\n")
        finally:
            # CRITICAL: clear buffered keystrokes before returning to shell
            try:
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
            except Exception:
                pass
        
        print("\n" + "="*50)
        print(f"Game Over! Final Score: {self.score} points")
        print(f"Total Questions: {self.total_questions}")
        print("="*50)


def main():
    # You can modify these settings
    DATA_FILE = "Scientists/17th_century.txt"
    DELAY_BETWEEN_FACTS = 3  # seconds
    
    # Check if data file exists
    if not Path(DATA_FILE).exists():
        print(f"Error: {DATA_FILE} not found.")
        print("Please create a data file with the following format:")
        print("""
Subject Name
- Fact 1
- Fact 2
- Fact 3

Another Subject
- Fact 1
- Fact 2
        """)
        sys.exit(1)
    
    game = QuizGame(DATA_FILE, delay_between_facts=DELAY_BETWEEN_FACTS)
    game.play_interactive()


if __name__ == "__main__":
    main()
