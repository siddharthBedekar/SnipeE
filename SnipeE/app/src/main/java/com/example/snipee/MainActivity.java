package com.example.snipee;


import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Rect;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import io.socket.client.IO;
import io.socket.client.Socket;

import java.net.URISyntaxException;


public class MainActivity extends AppCompatActivity {
    private float scaleFactorX, scaleFactorY;
    private int striker_len;
    private int puck_len;
    private Socket socket;
    private int screenBoundX, screenBoundY;
//    private Coord_filter puckfilter;    //moving average filter
//    private Coord_filter robotfilter;    //moving average filter
//    private Coord_filter humanfilter;    //moving average filter
//    private Coord_Interpolator interp; //interpolator
    private Rect bound;
    private boolean dataValid;

    private float desiredX, desiredY;

    //CONSTANTS
    final int CAM_X = 640;
    final int CAM_Y = 480;
    final int FILTER_WINDOW_SIZE = 2;
    final String ALY_URI = "http://192.168.1.84:5000";
    final String NOUB_URI = "http://192.168.1.65:5000";
    final String SERVER_URI = NOUB_URI;
    final int BOUND_MARGIN_X = 92;
    final int BOUND_MARGIN_Y = 319;
    final int CENTER_X = 544;
    final int CENTER_Y = 1882;
    final int BOUND_OFFSET = 175;



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // remove title and make fullscreen
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);

//        this.puckfilter = new Coord_filter(FILTER_WINDOW_SIZE);
//        this.robotfilter = new Coord_filter(FILTER_WINDOW_SIZE);
//        this.humanfilter = new Coord_filter(FILTER_WINDOW_SIZE);
//        this.interp = new Coord_Interpolator();
        this.configureScaling();
        this.socket = initSocket();
        this.bound = new Rect( BOUND_MARGIN_X, (screenBoundY/2)+BOUND_MARGIN_Y+BOUND_OFFSET,
                screenBoundX-BOUND_MARGIN_X, screenBoundY-BOUND_MARGIN_Y+BOUND_OFFSET);
        this.attachTouchListeners();
        this.attachSocketListeners();   //for server to client socket comms
    }

    @Override
    protected void onStart() {
        super.onStart();
        //main menu
        this.runGame();
    }

    @Override
    protected void onStop() {
        super.onStop();
//        this.socket.disconnect(); //find appropriate place to put this!
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
    }

    //--------------------------Game Methods-------------------------
    private void runGame(){
        //Socket init
        this.socket.connect();
    }

    @SuppressLint("ClickableViewAccessibility")
    private void attachTouchListeners(){

        ImageView userStriker = findViewById(R.id.userStriker);
        userStriker.setOnTouchListener((v, event) -> {
            final int action = event.getAction();

            switch (action & MotionEvent.ACTION_MASK) {
                case MotionEvent.ACTION_DOWN: {
                    break;
                }

                case MotionEvent.ACTION_MOVE: {
                    float newX, newY;
                    float half = (float)this.striker_len/2;

                    newX = event.getRawX();
                    newY = event.getRawY();
//                    Log.d("test1", bound.left + "," + bound.top + "," + bound.right + "," + bound.bottom + "||||" + newX + ", " + newY);

                    if (newX > this.bound.right){
                        newX = this.bound.right;
                    }
                    else if(newX < this.bound.left){
                        newX = this.bound.left;
                    }

                    if (newY > this.bound.bottom+half){
                        newY =  this.bound.bottom+half;
                    }
                    else if(newY < this.bound.top+half){
                        newY = this.bound.top+half;
                    }
                    this.dataValid = newX>=bound.left && newX<=bound.right && newY>=bound.top+half && newY<=bound.bottom+half;
//                    Log.d("test", Boolean.toString(dataValid));
//                    Log.d("test2", Integer.toString(screenBoundX) + ", " + Integer.toString(screenBoundY));
                    this.desiredX = (newX);
                    this.desiredY = (newY-half);
                    userStriker.setX(newX-half);
                    userStriker.setY(newY-half*2);
                    break;
                }
            }
            return true;
        });
    }

    //--------------------------Socket Methods-------------------------
    private Socket initSocket(){
        try {
            return IO.socket(SERVER_URI);
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }

    private void attachSocketListeners(){
        // Attach event listeners for sockets

        // CONNECT EVENT----------------------------------------------------------------------------
        socket.on(Socket.EVENT_CONNECT, args -> {
            String s = Build.PRODUCT + " Connected";
            socket.emit("message", s);
            runOnUiThread(() -> Toast.makeText(getActivity(), "Connected to " + SERVER_URI,
                                                Toast.LENGTH_SHORT).show());
        });

        // PERSONAL PING TEST EVENT-----------------------------------------------------------------
        socket.on("customPing", args -> socket.emit("customPong","got it"));

        // PUCK POSITION UPDATE---------------------------------------------------------------------
        socket.on("updatePuck", args -> {
            ImageView puck = findViewById(R.id.puck);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                                        Float.parseFloat(params[1]));

//            //apply filter
//            newCoords = puckfilter.getFilteredCoords(newCoords[0],
//                                                 newCoords[1]);

//            //apply interpolation
//            newCoords = interp.interpolate(newCoords[0],
//                                           newCoords[1]);

            puck.setX(newCoords[0]-((float)puck_len/2));
            puck.setY(newCoords[1]-((float)puck_len/2));
        });

        // ROBOT STRIKER POSITION UPDATE------------------------------------------------------------
        socket.on("updateRobot", args ->{
            //send desired robot striker location
            float[] scaledDesired = toServerScaling(this.desiredX,this.desiredY);
//            float[] scaledDesired = new float[2];
//            scaledDesired[0] = screenBoundX-desiredX;
//            scaledDesired[1] = desiredY;
//            Log.d("test", Boolean.toString(dataValid) + ", " +  this.desiredX + ", " + this.desiredY + ", " + this.startx + ", " + this.starty + ", " + (this.desiredX-this.startx) + ", " + (this.desiredY-this.starty));
            if (this.dataValid){
                socket.emit("desiredStrikerLocation", scaledDesired[0] +
                        "," + scaledDesired[1]);
                Log.d("test", scaledDesired[0] + ", " + scaledDesired[1]);
            }

            //receive new robot striker location
            ImageView robotStriker = findViewById(R.id.robotStriker);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                    Float.parseFloat(params[1]));

//            //apply filter
//            newCoords = robotfilter.getFilteredCoords(newCoords[0],
//                    newCoords[1]);

//            //apply interpolation
//            newCoords = interp.interpolate(newCoords[0],
//                    newCoords[1]);

            robotStriker.setX(newCoords[0]-((float)striker_len/2));
            robotStriker.setY(newCoords[1]-((float)striker_len/2));
        });

        // HUMAN STRIKER POSITION UPDATE------------------------------------------------------------
        socket.on("updateHuman", args ->{
            ImageView humanStriker = findViewById(R.id.opponentStriker);
            //split args into two strings
            String paramString = (String) args[0];
            String[] params = (paramString).split(",");

            float[] newCoords;

            //apply scaling
            newCoords = toClientScaling(Float.parseFloat(params[0]),
                    Float.parseFloat(params[1]));

//            //apply filter
//            newCoords = humanfilter.getFilteredCoords(newCoords[0],
//                    newCoords[1]);

//            //apply interpolation
//            newCoords = interp.interpolate(newCoords[0],
//                    newCoords[1]);

            humanStriker.setX(newCoords[0]-((float)striker_len/2));
            humanStriker.setY(newCoords[1]-((float)striker_len/2));
        });

        // DISCONNECT EVENT-------------------------------------------------------------------------
        socket.on(Socket.EVENT_DISCONNECT, args -> {
            String s = Build.PRODUCT + " Disconnected";
            socket.emit("message", s);
            runOnUiThread(() -> Toast.makeText(getActivity(),
                                "Disconnected from " + SERVER_URI,
                                Toast.LENGTH_SHORT).show());
        });
    }

    //--------------------------Scaling Methods-------------------------
    private float[] toServerScaling(float clientX, float clientY){
        //scale to server coordinates
        float[] result = new float[2];

        // swap x and y, and swap origin for x
        result[0] = (screenBoundY-clientY)/this.scaleFactorY;
        result[1] = clientX/this.scaleFactorX;
//        Log.d("test", scaleFactorX + ", " + scaleFactorY);
        return result;
    }

    private float[] toClientScaling(float serverX, float serverY){
        //scale to client coordinates
        float[] result = new float[2];

        //change orientation
        //subtract to make origin top left for mobile client
        result[0] =  serverY*this.scaleFactorX;
        result[1] = this.screenBoundY - serverX*this.scaleFactorY;
        return result;
    }

    private void configureScaling(){
        //initiate bounds
        this.screenBoundX = getDisplayDimensionX();
        this.screenBoundY = getDisplayDimensionY();

        //scaling and parameters
        this.scaleFactorX = (float)this.screenBoundX/CAM_Y; //rotated 90 deg
        this.scaleFactorY = (float)this.screenBoundY/CAM_X; //rotated 90 deg
//        Log.d("test", screenBoundX +" "+ screenBoundY);
        int goal_len = Math.round((float) this.screenBoundX / 3);
        this.striker_len = (goal_len /2);
        this.puck_len = (int) Math.round(this.striker_len/1.2);

        //make goal size to scale
        ImageView semicircle_d = findViewById(R.id.down_semicircle);
        semicircle_d.getLayoutParams().width = goal_len;
        semicircle_d.requestLayout();

        ImageView semicircle_u = findViewById(R.id.up_semicircle);
        semicircle_u.getLayoutParams().width = goal_len;
        semicircle_u.requestLayout();

        //make striker, and puck size to scale:
        ImageView userStriker = findViewById(R.id.userStriker);
        RelativeLayout.LayoutParams robotparams = new RelativeLayout.LayoutParams(
                RelativeLayout.LayoutParams.WRAP_CONTENT,
                RelativeLayout.LayoutParams.WRAP_CONTENT
        );
        int half = Math.round(striker_len/2);
        robotparams.setMargins(CENTER_X-half, CENTER_Y-half, CENTER_X-half, CENTER_Y-half);
        userStriker.setLayoutParams(robotparams);
        userStriker.getLayoutParams().height = this.striker_len;
        userStriker.getLayoutParams().width = this.striker_len;
        userStriker.requestLayout(); //apply the above changes to layout

        ImageView opponentStriker = findViewById(R.id.opponentStriker);
        opponentStriker.getLayoutParams().height = this.striker_len;
        opponentStriker.getLayoutParams().width = this.striker_len;
        opponentStriker.requestLayout();

        ImageView robotStriker = findViewById(R.id.robotStriker);
        robotStriker.getLayoutParams().height = this.striker_len;
        robotStriker.getLayoutParams().width = this.striker_len;
        robotStriker.requestLayout();

        RelativeLayout.LayoutParams params = new RelativeLayout.LayoutParams(
                RelativeLayout.LayoutParams.MATCH_PARENT,
                RelativeLayout.LayoutParams.MATCH_PARENT
        );
        params.setMargins(BOUND_MARGIN_X, screenBoundY/2 + BOUND_MARGIN_Y+BOUND_OFFSET, BOUND_MARGIN_X, BOUND_MARGIN_Y-BOUND_OFFSET);
        TextView mybox = findViewById(R.id.mybox);
        mybox.setLayoutParams(params);

        ImageView puck = findViewById(R.id.puck);
        puck.getLayoutParams().height = this.puck_len;
        puck.getLayoutParams().width = this.puck_len;
        puck.requestLayout();

    }


    //--------------------------Getters and Setters-------------------------
    public Activity getActivity(){
        return this;
    }

    private int getDisplayDimensionX(){
        return getResources().getDisplayMetrics().widthPixels;
    }

    private int getDisplayDimensionY(){
        return getResources().getDisplayMetrics().heightPixels;
    }

}

