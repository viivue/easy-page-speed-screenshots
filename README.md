# Easy Page Speed Screenshot

## Dependencies

- Selenium: `pip install selenium`
- Request: `pip install requests`

## Code Overview

The program will run by `main()` function

### Side function

- `send_link_for_test(link)`: Send the input data `link` to all tools for testing
  - `submit_link(tool, link, input_selector = '', form_selector = '')`: Submit the input of that tool, specify the selector because some page can be different
  - `get_res_link()`: Get the result link without encoded
- `user_input()`: Get user input and run the testing process, this function also set the `input_link` global variable
- `add_form_factor(links)`: add `form_factor` param to **Google Page Speed** links
- `execute_screenshot(links)`: execute taking screenshot with result after process with `user_input()`
  - `replace_url(url)`: replace some charactor in link into `-`
  - `is_tool(link, tool)`: check if the `link` belong to `tool`
  - `take_screenshot(file_name)`: take screenshot and save the file with `file_name`
  - `gen_file_name(number, tools, file_name, form_factor = '')`: generate `file_name`

## Current Result

Testing url: https://en.wikipedia.org/wiki/Main_Page

Result in terminal:

![](https://i.imgur.com/WOQwbAw.png)

Screenshot result:

![](https://i.imgur.com/77jWcRc.png)
