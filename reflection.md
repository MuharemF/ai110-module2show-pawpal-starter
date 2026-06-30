# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
my UML desgin will have a main class called "Petcare" and multiple other classes for each task that inharent the attributes of the "Petcare" class as well as a constrants class 
- What classes did you include, and what responsibilities did you assign to each?
Main class:  Petcare: holds a list of task, holds owner constraints,ownerName
class: careTask: attributes:  petName,taskName, start, duration, priority, manditory.
class: owner constrants: maxFreeTime, preferences 

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
 I only really had to had to change from daily to weekly as it made more sense for the user to create it for the upcoming week 
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
time and priority as if there is no time for a task but its not mandotiry then that task will not show up for the day 
- How did you decide which constraints mattered most?
time and priorrity were the most important because if something takes more time but isnt that important it can be skipped for the owner and done at a another time

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
cant have multiple owners with different pets this is reasonable cause I assume people who use this will make it for themselves 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
design brainstorming, debugging, refactoring I used it to get me ideas and boilerplate code and to check what issues could arise and what why a line isnt working 
- What kinds of prompts or questions were most helpful?
the more indepth lines where I ask look at this specifc file why is this giving an issue or I want to remove this option as the option makes no sense 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
the AI tried to suggest letting the user choose the schedule and then setting the recurrance which makes no sense so I had it remove the schedule builder and have it generate it on its own 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
edge cases such as not having a name/pet name or no task name or what would happen if there is a time conflict  
- Why were these tests important?
this is important cause these are the main things that people could forget or not realize that this is an issue for them

**b. Confidence**

- How confident are you that your scheduler works correctly?
on a scale of 1-10 with 10 being the most confident I would say 7 or 8 because their might be a edge case I did not forsee 
- What edge cases would you test next if you had more time?
I can not think of a specfice edge case that I have not tried 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
working with the AI despite some setbacks going more indepth on what I want and it producing it for me was more smooth then I thought it would be 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would redesign the UI as I am still not a huge fan of it 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
the start is easily the hardest part as coming up with a design and thinking about the layout from the get go is a struggle but once you can get going it and have a strong desgin it makes the buildding part done a lot faster.
