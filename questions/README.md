### Instructions

* `<Enter>` to generate next question
* `n` to question another person
* `q` to jump to group part

### Seeds

Seeds are constructed from files in the `seeds/` directory.

The file 

```
# seeds/human.txt

(as if you are leading a job interview)
Can you speak about your personal strengths?
Where do you see yourself in ten years?
What positive changes can you birng to this company?

[the necessity of human work]
Why is work so central for human life?
Why do humans build their identity around the work they do?
Why do people work so much?
Why do people have to work to have money?

What do you feel when you feel pain?
What do you feel when you are reading a poem about love?
Why do humans have to die?
```

is processed into a seed with prompts:

```
Write a list of questions as if you are leading a job interview:

1. Can you speak about your personal strengths?

2. Where do you see yourself in ten years?

3. What positive changes can you birng to this company?

4.
```

```
Write a list of questions about the necessity of human work:

1. Why is work so central for human life?

2. Why do humans build their identity around the work they do?

3. Why do people work so much?

4. Why do people have to work to have money?

5.
```

```
Write a list of question in a similar theme:

1. What do you feel when you feel pain?
 
2. What do you feel when you are reading a poem about love?

3. Why do humans have to die?

4.
```