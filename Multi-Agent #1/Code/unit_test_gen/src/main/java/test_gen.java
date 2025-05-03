import java.util.*;
import java.io.FileWriter;
import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

public class test_gen {

    // === Insert your original function(s) here ===
    public static class FIND_EQUAL_POINT_STRING_BRACKETS {
        static int f_gold(String str) {
            int len = str.length();
            int open[] = new int[len + 1];
            int close[] = new int[len + 1];
            int index = -1;
            open[0] = 0;
            close[len] = 0;
            if (str.charAt(0) == '(') open[1] = 1;
            if (str.charAt(len - 1) == ')') close[len - 1] = 1;
            for (int i = 1; i < len; i++) {
                if (str.charAt(i) == '(') open[i + 1] = open[i] + 1;
                else open[i + 1] = open[i];
            }
            for (int i = len - 2; i >= 0; i--) {
                if (str.charAt(i) == ')') close[i] = close[i + 1] + 1;
                else close[i] = close[i + 1];
            }
            if (open[len] == 0) return len;
            if (close[0] == 0) return 0;
            for (int i = 0; i <= len; i++) if (open[i] == close[i]) index = i;
            return index;
        }
    }
    // =============================================

    public static void main(String[] args) {
        // === Define your test inputs ===
        List<Object[]> inputs = Arrays.asList(
            new Object[]{""},
            new Object[]{"("},
            new Object[]{")"},
            new Object[]{"()"},
            new Object[]{"(())"},
            new Object[]{"(()())"},
            new Object[]{"((()))"},
            new Object[]{"()()()"},
            new Object[]{"(()"},
            new Object[]{")("},
            new Object[]{"())"},
            new Object[]{"(()))"},
            new Object[]{"((())())"},
            new Object[]{"(()(()))"},
            new Object[]{"()(()())"},
            new Object[]{"(()))(()"},
            new Object[]{"((()())())"},
            new Object[]{"()(()(()))"},
            new Object[]{"((())(()))"},
            new Object[]{"(()()(()))"}
        );
        // ================================

        // Prepare for output
        JsonArray resultsArray = new JsonArray();
        Gson gson = new Gson();

        // Iterate over all inputs
        for (Object[] inputSet : inputs) {
            String str = (String) inputSet[0];

            JsonObject jsonObject = new JsonObject();
            JsonArray inputJsonArray = new JsonArray();

            // Add input to JSON array
            inputJsonArray.add(str);

            jsonObject.add("input", inputJsonArray);

            // Try running the function
            try {
                int result = FIND_EQUAL_POINT_STRING_BRACKETS.f_gold(str);
                jsonObject.addProperty("result", result);
            } catch (Exception e) {
                jsonObject.addProperty("error", e.toString());
            }

            resultsArray.add(jsonObject);
        }

        // Save to results.json
        String directory = "/Users/parsayoussefpour/Desktop/MEng - Translator/Milestone 2/";  //Do not change this line
        try (FileWriter writer = new FileWriter(directory + "results.json")) { //Do not change this line
            gson.toJson(resultsArray, writer);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}