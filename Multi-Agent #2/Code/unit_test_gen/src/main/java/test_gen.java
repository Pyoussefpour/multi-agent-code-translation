import java.util.*;
import java.io.FileWriter;
import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

public class test_gen {

    // === Insert your original function(s) here ===
    public static class PROGRAM_BINARY_DECIMAL_CONVERSION_1 {
        static int f_gold(String n) {
            String num = n;
            int dec_value = 0;
            int base = 1;
            int len = num.length();
            for (int i = len - 1; i >= 0; i--) {
                if (num.charAt(i) == '1') dec_value += base;
                base = base * 2;
            }
            return dec_value;
        }
    }
    // =============================================

    public static void main(String[] args) {
        // === Define your test inputs ===
        List<Object[]> inputs = Arrays.asList(
            new Object[]{"0"},
            new Object[]{"1"},
            new Object[]{"10"},
            new Object[]{"11"},
            new Object[]{"101"},
            new Object[]{"110"},
            new Object[]{"111"},
            new Object[]{"1001"},
            new Object[]{"1010"},
            new Object[]{"1100"},
            new Object[]{"1111"},
            new Object[]{"0001"},
            new Object[]{"0010"},
            new Object[]{"0101"},
            new Object[]{"0110"},
            new Object[]{"10000"},
            new Object[]{"10101"},
            new Object[]{"11011"},
            new Object[]{"11100"},
            new Object[]{"11111"}
        );
        // ================================

        // Prepare for output
        JsonArray resultsArray = new JsonArray();
        Gson gson = new Gson();

        // Iterate over all inputs
        for (Object[] inputSet : inputs) {
            String binaryString = (String) inputSet[0];

            JsonObject jsonObject = new JsonObject();
            JsonArray inputJsonArray = new JsonArray();

            // Add input to JSON array
            inputJsonArray.add(binaryString);

            jsonObject.add("input", inputJsonArray);

            // Try running the function
            try {
                int result = PROGRAM_BINARY_DECIMAL_CONVERSION_1.f_gold(binaryString);
                jsonObject.addProperty("result", result);
            } catch (Exception e) {
                jsonObject.addProperty("error", e.toString());
            }

            resultsArray.add(jsonObject);
        }

        // Save to results.json
        String directory = "/Users/parsayoussefpour/Desktop/MEng - Translator/Final_Milestone/";  //Do not change this line
        try (FileWriter writer = new FileWriter(directory + "results.json")) { //Do not change this line
            gson.toJson(resultsArray, writer);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}