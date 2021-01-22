package com.example.snipee;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;


public class MainActivity extends AppCompatActivity {
    private double scaleFactorX, scaleFactorY;
    private int goal_len;

    //board dimensions
    final int BOARD_X = 45;
    final int BOARD_Y = 120;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // remove title and make fullscreen
        //
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(new MyView(this));

        //scaling and parameters
        this.scaleFactorX = (float)getDisplayDimensionX()/BOARD_X;
        this.scaleFactorY = (float)getDisplayDimensionY()/BOARD_Y;
        this.goal_len = (BOARD_X*(int)scaleFactorX)/3;

        //scaling usage example
//        int boardX = 45;
//        int boardY = 120;
//        try{
//            int[] screenC = scaleCoordinates(scaleFactorX, scaleFactorY, boardX, boardY);
//            Log.d("test", Integer.toString(getDisplayDimensionY()));
//            Log.d("test", Integer.toString(screenC[1]));
//        }
//        catch(Exception e) {
//            Log.d("test", e.toString());
//        }

    }

    private int[] scaleCoordinates(double scaleX, double scaleY, int boardX, int boardY) throws Exception{
        if (boardX > BOARD_X || boardY > BOARD_Y){
            throw new Exception("Input coordinates out of bound.");
        }
        return new int[]{(int) Math.round(boardX * scaleX), (int) Math.round(boardY * scaleY)};
    }

    private int getDisplayDimensionX(){
        return getResources().getDisplayMetrics().widthPixels;
    }

    private int getDisplayDimensionY(){
        return getResources().getDisplayMetrics().heightPixels;
    }

    public class MyView extends View{
        // for drawing
        // https://stackoverflow.com/questions/17954596/how-to-draw-circle-by-canvas-in-android
        Paint paint = null;
        public MyView(Context context)
        {
            super(context);
            paint = new Paint();
        }

        @Override
        protected void onDraw(Canvas canvas)
        {
            super.onDraw(canvas);
//          setWillNotDraw(false);
            int x = getWidth();
            int y = getHeight();

            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.WHITE);
            canvas.drawPaint(paint);
            // Use Color.parseColor to define HTML colors
            //draw static surface markers
            paint.setColor(Color.parseColor("#CD5C5C"));
            canvas.drawCircle((float)x/2, (float)y/2, (float)goal_len/2, paint);
            canvas.drawCircle((float)x/2, (float)0,
                    (float)goal_len/2, paint); //divide 2 because radius
            canvas.drawCircle((float)x/2, (float)y,
                    (float)goal_len/2, paint); //divide 2 because radius
            paint.setStrokeWidth(10);
            canvas.drawLine((float)0, (float)y/2, (float)x, (float)y/2, paint);

        }
    }

}

